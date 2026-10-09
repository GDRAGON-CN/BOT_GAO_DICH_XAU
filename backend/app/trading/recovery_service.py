"""Durable Webhook Recovery Service processing pending events after crash or restart."""
import asyncio
from typing import List
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_broker
from app.core.constants import WebhookStatus
from app.database.session import AsyncSessionLocal
from app.models.webhook import WebhookEvent
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.trading_service import TradingService

class WebhookRecoveryService:
    """
    Scans the database for unfulfilled/pending WebhookEvent records (status=RECEIVED)
    persisted before a server restart or crash, and drains/recovers them safely.
    """

    @classmethod
    async def recover_pending_events(cls) -> int:
        """
        Processes any WebhookEvent in RECEIVED state upon application startup.
        Does NOT duplicate trades; validates against current market and bot state.
        Returns the number of recovered events.
        """
        recovered_count = 0
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(WebhookEvent).where(
                    WebhookEvent.processing_status == WebhookStatus.RECEIVED
                ).order_by(WebhookEvent.id.asc())
                result = await db.execute(stmt)
                pending_events: List[WebhookEvent] = list(result.scalars().all())

                if not pending_events:
                    logger.info("Durable Webhook Recovery: No pending unhandled webhooks found.")
                    return 0

                logger.info(f"Durable Webhook Recovery: Found {len(pending_events)} pending events to recover.")
                broker = get_broker()
                trading_service = TradingService(broker)

                # Ensure broker state is reconciled first
                from app.trading.reconciliation_service import ReconciliationService
                reconciler = ReconciliationService(broker)
                await reconciler.run_reconciliation(db)

                # Fetch live positions directly from broker to ensure no duplicate orders
                live_broker_positions = await broker.get_open_positions()
                broker_symbols_with_positions = {p.symbol.upper() for p in live_broker_positions}

                for event in pending_events:
                    try:
                        logger.info(f"Recovering pending WebhookEvent #{event.id} ({event.event_uuid})...")
                        payload = TradingViewWebhookSchema.model_validate(event.raw_payload)

                        # If broker already holds an open position on this symbol, do NOT blindly resubmit!
                        if payload.symbol.upper() in broker_symbols_with_positions:
                            msg = f"Recovery safety: Broker already holds open position for {payload.symbol}. Suppressing blind resubmission."
                            logger.warning(msg)
                            event.processing_status = WebhookStatus.REJECTED
                            event.rejection_reason = msg
                            await db.commit()
                            continue

                        success, message = await trading_service.handle_webhook_signal(
                            payload=payload,
                            webhook_event_id=event.id,
                            db=db
                        )
                        event.processing_status = WebhookStatus.PROCESSED if success else WebhookStatus.REJECTED
                        if not success:
                            event.rejection_reason = f"Recovery processing: {message}"
                        await db.commit()
                        recovered_count += 1
                        logger.info(f"Successfully processed pending event #{event.id}: {message}")
                    except Exception as item_err:
                        logger.error(f"Failed recovering pending event #{event.id}: {item_err}")
                        event.processing_status = WebhookStatus.FAILED
                        event.rejection_reason = f"Recovery failure: {item_err}"
                        await db.commit()

            except Exception as e:
                logger.error(f"Durable Webhook Recovery encountered error querying DB: {e}")

        return recovered_count

webhook_recovery_service = WebhookRecoveryService()
