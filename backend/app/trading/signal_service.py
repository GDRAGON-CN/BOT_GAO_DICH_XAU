"""Signal parsing, validation, and creation service."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from app.core.constants import OrderSide, SignalStatus
# pyrefly: ignore [missing-import]
from app.models.signal import Signal
# pyrefly: ignore [missing-import]
from app.schemas.signal import SignalDTO
# pyrefly: ignore [missing-import]
from app.schemas.webhook import TradingViewWebhookSchema

class SignalService:
    """Validates raw incoming signals and constructs canonical Signal objects."""

    ALLOWED_ACTIONS = {OrderSide.BUY, OrderSide.SELL}

    def validate_payload(self, payload: TradingViewWebhookSchema) -> Tuple[bool, Optional[str]]:
        """
        Validates signal integrity:
        - Symbol must be non-empty
        - Action must be strictly BUY or SELL
        - Mandatory Stop Loss must be present and positive
        - Risk percent cannot exceed configured MAX_RISK_PERCENT_PER_TRADE (clamped or rejected)
        """
        from app.core.config import settings

        if not payload.symbol or not payload.symbol.strip():
            return False, "Symbol is required and cannot be empty"

        if payload.action not in self.ALLOWED_ACTIONS:
            return False, f"Action '{payload.action}' is rejected. Only BUY and SELL are supported for trade signals."

        if payload.sl is None or payload.sl <= 0:
            return False, "Stop loss (SL) is strictly required and must be positive"

        if payload.price is not None and payload.price <= 0:
            return False, "Entry price must be positive if specified"

        if payload.tp is not None and payload.tp <= 0:
            return False, "Take profit (TP) must be positive if specified"

        if payload.risk_percent is not None:
            if payload.risk_percent <= 0:
                return False, "Risk percentage must be positive"
            if payload.risk_percent > settings.MAX_RISK_PERCENT_PER_TRADE:
                logger.warning(
                    f"Payload risk_percent {payload.risk_percent}% exceeds limit {settings.MAX_RISK_PERCENT_PER_TRADE}%. "
                    f"Capping to {settings.MAX_RISK_PERCENT_PER_TRADE}%."
                )
                payload.risk_percent = settings.MAX_RISK_PERCENT_PER_TRADE

        return True, None

    async def create_signal(
        self,
        payload: TradingViewWebhookSchema,
        webhook_event_id: Optional[int],
        db: AsyncSession
    ) -> Tuple[Signal, SignalDTO]:
        """Creates and persists a canonical Signal record in the database."""
        signal_uuid = str(uuid.uuid4())
        is_valid, validation_error = self.validate_payload(payload)

        status = SignalStatus.PENDING if is_valid else SignalStatus.FAILED
        rejection_reason = validation_error

        db_signal = Signal(
            webhook_event_id=webhook_event_id,
            signal_uuid=signal_uuid,
            symbol=payload.symbol.upper().strip(),
            timeframe=payload.timeframe or "M15",
            action=payload.action,
            target_price=Decimal(str(payload.price)) if payload.price is not None else None,
            stop_loss=Decimal(str(payload.sl)) if payload.sl is not None else None,
            take_profit=Decimal(str(payload.tp)) if payload.tp is not None else None,
            status=status,
            rejection_reason=rejection_reason,
            created_at=datetime.utcnow()
        )
        db.add(db_signal)
        await db.flush()

        signal_dto = SignalDTO(
            id=db_signal.id,
            signal_uuid=signal_uuid,
            symbol=payload.symbol.upper().strip(),
            timeframe=payload.timeframe or "M15",
            action=payload.action,
            entry=payload.price,
            stop_loss=payload.sl,
            take_profit=payload.tp,
            strategy=payload.strategy_name or "GoldBot_EMA_ATR",
            source="TradingView",
            webhook_event_id=webhook_event_id,
            timestamp=datetime.utcnow(),
            status=status,
            rejection_reason=rejection_reason,
            created_at=db_signal.created_at
        )

        return db_signal, signal_dto
