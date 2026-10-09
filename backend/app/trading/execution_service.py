"""ExecutionService managing pre-trade gating, broker dispatch, and post-trade state persistence."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
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
from app.schemas.order import OrderExecutionResultDTO, OrderRequestDTO
from app.schemas.signal import SignalDTO
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.broker_service import BrokerService
from app.trading.position_service import PositionService
from app.trading.risk_service import RiskService
from app.trading.session_service import TradingSessionService

class ExecutionService:
    """
    Coordinates pre-execution validations, order submission, fail-safe uncertain handling,
    and post-trade database persistence.
    """

    def __init__(
        self,
        broker_service: BrokerService,
        risk_service: RiskService,
        position_service: PositionService,
        session_service: TradingSessionService
    ):
        self.broker = broker_service
        self.risk = risk_service
        self.positions = position_service
        self.sessions = session_service

    async def execute_signal(
        self,
        signal_entity: Signal,
        signal_dto: SignalDTO,
        payload: TradingViewWebhookSchema,
        db: AsyncSession
    ) -> Tuple[bool, str]:
        """
        Executes order following strict sequence:
        1. Market & Connection Validation
        2. Session Validation
        3. Spread Validation
        4. Account & Symbol Specs
        5. Position Limits
        6. Risk & Lot Validation
        7. Order Dispatch
        8. Result Verification & Fail-safe Handling
        9. Persistence & Notification
        """
        # 1. Connection check
        connected = await self.broker.ensure_connected()
        if not connected:
            reason = "Broker is disconnected from MetaTrader 5 terminal."
            logger.error(reason)
            signal_entity.status = SignalStatus.FAILED
            signal_entity.rejection_reason = reason
            await db.commit()
            return False, reason

        # 2. Session Validation
        is_active, session_name = self.sessions.is_session_active()
        if not is_active:
            reason = f"Trading session inactive: {session_name}"
            logger.warning(reason)
            signal_entity.status = SignalStatus.REJECTED_SESSION
            signal_entity.rejection_reason = reason
            await db.commit()
            return False, reason

        # 3. Market Quote & Spread Validation
        quote = await self.broker.get_current_quote(payload.symbol)
        spread_valid, current_spread, spread_msg = self.sessions.validate_spread(quote)
        if not spread_valid:
            logger.warning(spread_msg)
            signal_entity.status = SignalStatus.REJECTED_RISK
            signal_entity.rejection_reason = spread_msg

            risk_evt = RiskEvent(
                signal_id=signal_entity.id,
                event_type=RiskEventType.SPREAD_EXCEEDED,
                rule_name="MAX_SPREAD_POINTS",
                threshold_value=str(settings.MAX_SPREAD_POINTS),
                actual_value=str(current_spread),
                system_action_taken=RiskAction.SIGNAL_REJECTED
            )
            db.add(risk_evt)
            await db.commit()
            return False, spread_msg

        # 4. Symbol specs and Account info
        account = await self.broker.get_account_info()
        symbol_info = await self.broker.get_symbol_info(payload.symbol)
        if not symbol_info:
            reason = f"Symbol '{payload.symbol}' not found on broker."
            logger.error(reason)
            signal_entity.status = SignalStatus.FAILED
            signal_entity.rejection_reason = reason
            await db.commit()
            return False, reason

        # 5. Position Limits
        open_positions = await self.positions.get_active_positions(payload.symbol)
        if len(open_positions) >= settings.MAX_OPEN_POSITIONS:
            reason = f"Position limit reached: {len(open_positions)} >= {settings.MAX_OPEN_POSITIONS}"
            logger.warning(reason)
            signal_entity.status = SignalStatus.REJECTED_RISK
            signal_entity.rejection_reason = reason

            risk_evt = RiskEvent(
                signal_id=signal_entity.id,
                event_type=RiskEventType.BOT_STATE_RESTRICTION,
                rule_name="MAX_OPEN_POSITIONS",
                threshold_value=str(settings.MAX_OPEN_POSITIONS),
                actual_value=str(len(open_positions)),
                system_action_taken=RiskAction.SIGNAL_REJECTED
            )
            db.add(risk_evt)
            await db.commit()
            return False, reason

        # 6. Risk Engine & Lot Validation
        risk_res = await self.risk.validate_signal(
            payload=payload,
            account=account,
            symbol_info=symbol_info,
            open_positions_count=len(open_positions),
            daily_loss_realized=0.0
        )

        if not risk_res.is_valid:
            reason = risk_res.reason or "Risk validation failed"
            logger.warning(f"Signal rejected by risk: {reason}")
            signal_entity.status = SignalStatus.REJECTED_RISK
            signal_entity.rejection_reason = reason

            risk_evt = RiskEvent(
                signal_id=signal_entity.id,
                event_type=RiskEventType.INVALID_LOT_SIZE if "lot" in (risk_res.rule_name or "") else RiskEventType.BOT_STATE_RESTRICTION,
                rule_name=risk_res.rule_name or "RISK_VALIDATION",
                threshold_value="",
                actual_value="",
                system_action_taken=risk_res.action_taken or RiskAction.SIGNAL_REJECTED,
                details={"reason": reason}
            )
            db.add(risk_evt)
            await db.commit()

            telegram_bot.notify_risk_rejection(
                rule_name=risk_res.rule_name or "RISK_VALIDATION",
                details=f"{payload.symbol} {payload.action.value} - {reason}"
            )
            return False, reason

        # 7. Broker Order Dispatch
        order_req = OrderRequestDTO(
            symbol=payload.symbol,
            side=payload.action,
            lots=risk_res.calculated_lots,
            stop_loss=payload.sl,
            take_profit=payload.tp,
            deviation_points=settings.MAX_SLIPPAGE_POINTS,
            magic=123456,
            comment=f"Sig_{signal_entity.signal_uuid[:8]}"
        )

        # Notify Telegram: Order Submitted
        telegram_bot.notify_order_submitted(
            symbol=payload.symbol,
            action=payload.action.value,
            lots=risk_res.calculated_lots,
            price=payload.price
        )

        exec_res: OrderExecutionResultDTO = await self.broker.execute_market_order(order_req)

        # 8. Check Execution Status & Fail-Safe Uncertain Mechanism
        # If retcode indicates network timeout, uncertain execution, or unknown failure
        is_uncertain = exec_res.retcode in {10004, 10006, 10007, 10018, 10024} # Requote, Connection, Timeout, etc.

        if is_uncertain:
            warning_msg = f"UNCERTAIN execution for order: retcode={exec_res.retcode}, msg={exec_res.error_message}. DO NOT resubmit."
            logger.error(warning_msg)

            uncertain_order = Order(
                signal_id=signal_entity.id,
                broker_order_ticket=exec_res.order_ticket or 0,
                symbol=symbol_info.name,
                order_type=payload.action,
                requested_lots=Decimal(str(risk_res.calculated_lots)),
                filled_lots=Decimal("0.0"),
                requested_price=Decimal(str(payload.price or quote.bid)),
                execution_price=None,
                slippage_points=Decimal("0.0"),
                stop_loss=Decimal(str(payload.sl)) if payload.sl else None,
                take_profit=Decimal(str(payload.tp)) if payload.tp else None,
                execution_retcode=exec_res.retcode,
                execution_status=OrderStatus.UNCERTAIN,
                submitted_at=datetime.utcnow()
            )
            db.add(uncertain_order)
            signal_entity.status = SignalStatus.FAILED
            signal_entity.rejection_reason = warning_msg
            await db.commit()

            telegram_bot.notify_async(f"🚨 *UNCERTAIN ORDER*: {warning_msg} Requires manual reconciliation.")
            return False, warning_msg

        if not exec_res.success:
            err_msg = exec_res.error_message or "Order execution rejected by broker"
            logger.error(f"Execution failed: {err_msg}")
            signal_entity.status = SignalStatus.FAILED
            signal_entity.rejection_reason = err_msg

            failed_order = Order(
                signal_id=signal_entity.id,
                broker_order_ticket=exec_res.order_ticket or 0,
                symbol=symbol_info.name,
                order_type=payload.action,
                requested_lots=Decimal(str(risk_res.calculated_lots)),
                filled_lots=Decimal("0.0"),
                requested_price=Decimal(str(payload.price or quote.bid)),
                execution_price=None,
                slippage_points=Decimal("0.0"),
                stop_loss=Decimal(str(payload.sl)) if payload.sl else None,
                take_profit=Decimal(str(payload.tp)) if payload.tp else None,
                execution_retcode=exec_res.retcode,
                execution_status=OrderStatus.REJECTED,
                submitted_at=datetime.utcnow()
            )
            db.add(failed_order)
            await db.commit()
            return False, err_msg

        # 9. Successful Execution Persistence
        db_order = Order(
            signal_id=signal_entity.id,
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

        signal_entity.status = SignalStatus.EXECUTED
        await db.commit()

        # Update telemetry
        from app.monitoring.telemetry import telemetry
        telemetry.record_execution()

        # Send Telegram notifications for order filled and position opened
        ticket_no = exec_res.order_ticket or 0
        fill_price = float(db_order.execution_price)
        filled_lots = float(db_order.filled_lots)
        telegram_bot.notify_order_filled(
            ticket=ticket_no,
            symbol=symbol_info.name,
            action=payload.action.value,
            lots=filled_lots,
            fill_price=fill_price
        )
        telegram_bot.notify_position_opened(
            ticket=db_pos.broker_position_ticket,
            symbol=symbol_info.name,
            side=db_pos.side.value,
            lots=filled_lots,
            entry=fill_price,
            sl=float(db_order.stop_loss) if db_order.stop_loss else None,
            tp=float(db_order.take_profit) if db_order.take_profit else None
        )

        logger.info(f"Order #{exec_res.order_ticket} executed and stored.")
        return True, "FILLED"

