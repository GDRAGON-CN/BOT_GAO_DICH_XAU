"""Orchestrator trading service tying all modular components together."""
from typing import Optional, Tuple
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.brokers.base import IBrokerAdapter
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.broker_service import BrokerService
from app.trading.deduplication import deduplication_service
from app.trading.execution_service import ExecutionService
from app.trading.position_service import PositionService
from app.trading.risk_service import RiskService
from app.trading.session_service import trading_session_service
from app.trading.signal_service import SignalService

class TradingService:
    """
    Main entry point for trading operations orchestrating the strict sequence:
    TradingView Signal
    ↓
    Signal Validation (SignalService)
    ↓
    Trading Session (TradingSessionService)
    ↓
    Risk Engine (RiskService)
    ↓
    Position Validation (PositionService)
    ↓
    Execution Engine (ExecutionService)
    ↓
    Broker Adapter (BrokerService)
    ↓
    MT5
    ↓
    Vantage
    """

    def __init__(self, broker: IBrokerAdapter):
        self.broker_service = BrokerService(broker)
        self.signal_service = SignalService()
        self.session_service = trading_session_service
        self.risk_service = RiskService(broker)
        self.position_service = PositionService(broker)
        self.execution_service = ExecutionService(
            broker_service=self.broker_service,
            risk_service=self.risk_service,
            position_service=self.position_service,
            session_service=self.session_service
        )
        self.deduplication = deduplication_service

    async def handle_webhook_signal(
        self,
        payload: TradingViewWebhookSchema,
        webhook_event_id: Optional[int],
        db: AsyncSession
    ) -> Tuple[bool, str]:
        from app.notifications.telegram_bot import telegram_bot
        # Send Telegram new signal notification
        telegram_bot.notify_new_signal(
            symbol=payload.symbol,
            action=payload.action.value if hasattr(payload.action, "value") else str(payload.action),
            timeframe=payload.timeframe or "M15",
            entry=payload.price,
            sl=payload.sl,
            tp=payload.tp
        )

        # 1. Parse and create canonical signal
        signal_entity, signal_dto = await self.signal_service.create_signal(
            payload=payload,
            webhook_event_id=webhook_event_id,
            db=db
        )

        # 2. Check if signal was rejected upfront due to invalid schema/action/missing SL
        if signal_entity.rejection_reason:
            logger.warning(f"Signal rejected upfront: {signal_entity.rejection_reason}")
            telegram_bot.notify_signal_rejected(
                symbol=payload.symbol,
                action=payload.action.value if hasattr(payload.action, "value") else str(payload.action),
                reason=signal_entity.rejection_reason
            )
            await db.commit()
            return False, signal_entity.rejection_reason


        # 3. Dispatch through execution pipeline
        success, message = await self.execution_service.execute_signal(
            signal_entity=signal_entity,
            signal_dto=signal_dto,
            payload=payload,
            db=db
        )

        return success, message
