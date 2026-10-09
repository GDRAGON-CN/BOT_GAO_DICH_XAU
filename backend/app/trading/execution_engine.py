import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.brokers.base import IBrokerAdapter
from app.core.config import settings
from app.core.constants import (
    OrderSide,
    OrderStatus,
    PositionSide,
    PositionStatus,
    RiskAction,
    RiskEventType,
    SignalStatus,
)
from app.models.order import Order
from app.models.position import Position
from app.models.risk import RiskEvent
from app.models.signal import Signal
from app.notifications.telegram_bot import telegram_bot
from app.schemas.order import OrderRequestDTO
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.position_manager import PositionManager
from app.trading.risk_engine import RiskEngine
from app.trading.session_validator import session_validator

class ExecutionEngine:
    """Coordinates signal gating, risk approval, broker execution, and persistence."""

    def __init__(self, broker: IBrokerAdapter):
        self.broker = broker
        self.risk_engine = RiskEngine(broker)
        self.position_manager = PositionManager(broker)

    async def process_signal(
        self,
        payload: TradingViewWebhookSchema,
        webhook_event_id: Optional[int],
        db: AsyncSession
    ) -> bool:
        signal_uuid = str(uuid.uuid4())
        logger.info(f"Processing signal [{signal_uuid}]: {payload.action} {payload.symbol}")

        # 1. Create DB Signal entity
        db_signal = Signal(
            webhook_event_id=webhook_event_id,
            signal_uuid=signal_uuid,
            symbol=payload.symbol.upper(),
            timeframe=payload.timeframe,
            action=payload.action,
            target_price=Decimal(str(payload.price)) if payload.price else None,
            stop_loss=Decimal(str(payload.sl)) if payload.sl else None,
            take_profit=Decimal(str(payload.tp)) if payload.tp else None,
            status=SignalStatus.PENDING
        )
        db.add(db_signal)
        await db.flush()

        # 2. Session & Spread Validation
        is_active, session_name = session_validator.is_session_active()
        if not is_active:
            rejection_msg = f"Trading session inactive: {session_name}"
            logger.warning(rejection_msg)
            db_signal.status = SignalStatus.REJECTED_SESSION
            db_signal.rejection_reason = rejection_msg
            await db.commit()
            return False

        quote = await self.broker.get_current_quote(payload.symbol)
        spread_valid, current_spread, spread_reason = session_validator.validate_spread(quote)
        if not spread_valid:
            logger.warning(spread_reason)
            db_signal.status = SignalStatus.REJECTED_RISK
            db_signal.rejection_reason = spread_reason

            risk_evt = RiskEvent(
                signal_id=db_signal.id,
                event_type=RiskEventType.SPREAD_EXCEEDED,
                rule_name="MAX_SPREAD_POINTS",
                threshold_value=str(settings.MAX_SPREAD_POINTS),
                actual_value=str(current_spread),
                system_action_taken=RiskAction.SIGNAL_REJECTED
            )
            db.add(risk_evt)
            await db.commit()
            return False

        # 3. Retrieve broker state
        try:
            account = await self.broker.get_account_info()
            symbol_info = await self.broker.get_symbol_info(payload.symbol)
            if not symbol_info:
                raise RuntimeError(f"Symbol {payload.symbol} specs not found")
            open_positions = await self.broker.get_open_positions()
        except Exception as e:
            err = f"Broker query error: {e}"
            logger.error(err)
            db_signal.status = SignalStatus.FAILED
            db_signal.rejection_reason = err
            await db.commit()
            return False

        # 4. Handle CLOSE action directly
        if payload.action == OrderSide.CLOSE:
            logger.info(f"Closing open positions for {payload.symbol}")
            await self.position_manager.close_all_positions(payload.symbol)
            db_signal.status = SignalStatus.EXECUTED
            await db.commit()
            return True

        # 5. Risk Engine Validation
        risk_res = await self.risk_engine.validate_signal(
            payload=payload,
            account=account,
            symbol_info=symbol_info,
            open_positions_count=len(open_positions),
            daily_loss_realized=0.0
        )

        if not risk_res.is_valid:
            logger.warning(f"Signal rejected by risk engine: {risk_res.reason}")
            db_signal.status = SignalStatus.REJECTED_RISK
            db_signal.rejection_reason = risk_res.reason

            risk_evt = RiskEvent(
                signal_id=db_signal.id,
                event_type=RiskEventType.INVALID_LOT_SIZE if "lot" in (risk_res.rule_name or "") else RiskEventType.BOT_STATE_RESTRICTION,
                rule_name=risk_res.rule_name or "RISK_VALIDATION",
                threshold_value="",
                actual_value="",
                system_action_taken=risk_res.action_taken or RiskAction.SIGNAL_REJECTED,
                details={"reason": risk_res.reason}
            )
            db.add(risk_evt)
            await db.commit()

            telegram_bot.notify_async(
                f"⚠️ *RISK REJECTION*: {payload.symbol} {payload.action.value} - {risk_res.reason}"
            )
            return False

        # 6. Execute Order
        req = OrderRequestDTO(
            symbol=payload.symbol,
            side=payload.action,
            lots=risk_res.calculated_lots,
            stop_loss=payload.sl,
            take_profit=payload.tp,
            deviation_points=settings.MAX_SLIPPAGE_POINTS,
            magic=123456,
            comment=f"Signal {signal_uuid[:8]}"
        )

        exec_res = await self.broker.execute_market_order(req)
        if not exec_res.success:
            logger.error(f"Execution failed: {exec_res.error_message}")
            db_signal.status = SignalStatus.FAILED
            db_signal.rejection_reason = exec_res.error_message
            await db.commit()
            return False

        # 7. Persist Order and Position
        db_order = Order(
            signal_id=db_signal.id,
            broker_order_ticket=exec_res.order_ticket or 0,
            symbol=symbol_info.name,
            order_type=payload.action,
            requested_lots=Decimal(str(risk_res.calculated_lots)),
            filled_lots=Decimal(str(exec_res.lots or risk_res.calculated_lots)),
            requested_price=Decimal(str(payload.price or quote.bid)),
            execution_price=Decimal(str(exec_res.execution_price or quote.bid)),
            slippage_points=Decimal("0.0"),
            stop_loss=Decimal(str(payload.sl)) if payload.sl else None,
            take_profit=Decimal(str(payload.tp)) if payload.tp else None,
            execution_retcode=exec_res.retcode,
            execution_status=OrderStatus.FILLED,
            submitted_at=datetime.utcnow(),
            filled_at=datetime.utcnow()
        )
        db.add(db_order)
        await db.flush()

        db_pos = Position(
            broker_position_ticket=exec_res.position_ticket or exec_res.order_ticket or 0,
            opening_order_id=db_order.id,
            symbol=symbol_info.name,
            side=PositionSide.LONG if payload.action == OrderSide.BUY else PositionSide.SHORT,
            initial_lots=db_order.filled_lots,
            current_lots=db_order.filled_lots,
            entry_price=db_order.execution_price,
            current_stop_loss=db_order.stop_loss,
            current_take_profit=db_order.take_profit,
            status=PositionStatus.OPEN,
            opened_at=datetime.utcnow()
        )
        db.add(db_pos)
        db_signal.status = SignalStatus.EXECUTED
        await db.commit()

        # 8. Notify Telegram
        telegram_bot.notify_async(
            f"🚀 *ORDER FILLED*: #{exec_res.order_ticket} {payload.action.value} {db_order.filled_lots} {symbol_info.name} @ {db_order.execution_price}"
        )
        logger.info(f"Order #{exec_res.order_ticket} executed and stored.")
        return True
