import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_broker
from app.core.constants import WebhookStatus
from app.core.security import verify_webhook_token
from app.database.session import AsyncSessionLocal, get_db_session
from app.models.webhook import WebhookEvent
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.deduplication import deduplication_service
from app.trading.trading_service import TradingService

router = APIRouter(tags=["Webhook"])

async def _process_signal_async(event_id: int, payload: TradingViewWebhookSchema):
    """Internal asynchronous worker processing signal pipeline without blocking webhook HTTP response."""
    async with AsyncSessionLocal() as db:
        try:
            broker = get_broker()
            trading_service = TradingService(broker)
            success, message = await trading_service.handle_webhook_signal(
                payload=payload,
                webhook_event_id=event_id,
                db=db
            )
            # Update webhook event final status
            event = await db.get(WebhookEvent, event_id)
            if event:
                event.processing_status = WebhookStatus.PROCESSED if success else WebhookStatus.REJECTED
                if not success:
                    event.rejection_reason = message
                await db.commit()
            logger.info(f"Background signal processing finished for event #{event_id}: {message}")
        except Exception as exc:
            logger.error(f"Error in background signal worker for event #{event_id}: {exc}")
            try:
                event = await db.get(WebhookEvent, event_id)
                if event:
                    event.processing_status = WebhookStatus.FAILED
                    event.rejection_reason = str(exc)
                    await db.commit()
            except Exception:
                pass

async def _handle_webhook_request(
    payload: TradingViewWebhookSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str,
    db: AsyncSession
):
    # 1. Authenticate Secret
    verify_webhook_token(x_webhook_secret=x_webhook_secret, payload_secret=payload.secret)

    from app.monitoring.telemetry import telemetry
    telemetry.record_webhook()

    client_ip = request.client.host if request.client else "unknown"
    payload_dict = payload.model_dump()
    payload_hash = deduplication_service.compute_hash(payload_dict)

    # 2. Strict Timestamp Validation
    from app.trading.timestamp_validator import TimestampValidator
    if payload.timestamp or payload.bar_time:
        ts_to_check = payload.timestamp or payload.bar_time
        is_fresh, ts_err = TimestampValidator.validate_freshness(ts_to_check)
        if not is_fresh:
            logger.warning(f"Rejecting alert due to timestamp violation: {ts_err}")
            return {"status": "rejected", "reason": ts_err or "invalid_timestamp", "received": False}

    # 3. Fast In-Memory Deduplication Check
    is_dup, elapsed = deduplication_service.is_duplicate(payload_hash)
    if is_dup:
        logger.warning(f"Ignoring duplicate alert ({elapsed:.1f}s ago)")
        return {"status": "ignored", "reason": "duplicate_signal", "elapsed_seconds": elapsed, "received": True}

    # 4. Immediate Persistent Database Idempotency & Unique Constraint Enforcement
    from sqlalchemy.exc import IntegrityError
    from app.repositories.webhook_repo import WebhookRepository

    event_uuid = payload.event_id or str(uuid.uuid4())
    event = WebhookEvent(
        event_uuid=event_uuid,
        payload_hash=payload_hash,
        source_ip=client_ip,
        raw_payload=payload_dict,
        processing_status=WebhookStatus.RECEIVED
    )

    try:
        db.add(event)
        await db.commit()
        await db.refresh(event)
    except IntegrityError:
        # Handles concurrent duplicate webhooks and process restart recovery
        await db.rollback()
        logger.warning(f"Database idempotency constraint caught duplicate event: uuid={event_uuid}, hash={payload_hash[:10]}...")
        # Mark in local cache so future requests don't hit DB repeatedly
        deduplication_service.record_seen(payload_hash)

        # Check existing event status from database without resubmitting order
        webhook_repo = WebhookRepository(db)
        existing = await webhook_repo.get_by_hash(payload_hash)
        existing_status = existing.processing_status.value if existing else "DUPLICATE"

        return {
            "status": "ignored",
            "reason": "duplicate_event_key_or_hash",
            "existing_status": existing_status,
            "received": True
        }

    # Record seen in memory
    deduplication_service.record_seen(payload_hash)

    # 5. Fast Acknowledgement: Dispatch to Background Task (durable status already saved as RECEIVED in DB)
    background_tasks.add_task(_process_signal_async, event.id, payload)

    return {
        "status": "acknowledged",
        "event_uuid": event.event_uuid,
        "symbol": payload.symbol,
        "action": payload.action.value,
        "received": True
    }

@router.post("/webhook/tradingview", status_code=status.HTTP_200_OK)
@router.post("/webhooks/tradingview", status_code=status.HTTP_200_OK)
async def receive_tradingview_alert(
    payload: TradingViewWebhookSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(None, alias="X-Webhook-Secret"),
    db: AsyncSession = Depends(get_db_session)
):
    return await _handle_webhook_request(
        payload=payload,
        request=request,
        background_tasks=background_tasks,
        x_webhook_secret=x_webhook_secret,
        db=db
    )


