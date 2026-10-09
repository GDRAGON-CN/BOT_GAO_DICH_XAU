from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_broker
from app.brokers.base import IBrokerAdapter
from app.core.config import settings
from app.database.session import get_db_session
from app.models.audit import BotEvent
from app.models.order import Order
from app.models.position import Position
from app.models.risk import RiskEvent
from app.models.signal import Signal
from app.models.trade import Trade
from app.monitoring.metrics import MetricsAggregator
from app.repositories.order_repo import OrderRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.signal_repo import SignalRepository
from app.trading.state_manager import state_manager

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def get_metrics(
    broker: IBrokerAdapter = Depends(get_broker),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    aggregator = MetricsAggregator(
        broker=broker,
        signal_repo=SignalRepository(db),
        order_repo=OrderRepository(db),
        position_repo=PositionRepository(db)
    )
    summary = await aggregator.get_dashboard_summary()

    # Query recent trades, risk events, and bot events
    trades_res = await db.execute(select(Trade).order_by(desc(Trade.closed_at)).limit(10))
    trades = list(trades_res.scalars().all())

    risk_res = await db.execute(select(RiskEvent).order_by(desc(RiskEvent.created_at)).limit(10))
    risk_events = list(risk_res.scalars().all())

    bot_res = await db.execute(select(BotEvent).order_by(desc(BotEvent.created_at)).limit(10))
    bot_events = list(bot_res.scalars().all())

    # Calculate today's realized PnL
    today_pnl = sum(float(t.net_profit) for t in trades)
    daily_loss = abs(min(0.0, today_pnl))

    # Add bot & trading status
    summary["bot_state"] = state_manager.current_state.value
    summary["is_running"] = state_manager.is_running
    summary["trading_env"] = settings.TRADING_ENV
    summary["today_pnl"] = today_pnl
    summary["daily_loss"] = daily_loss

    summary["recent_trades"] = [
        {
            "id": t.id,
            "position_id": t.position_id,
            "close_price": float(t.close_price),
            "net_profit": float(t.net_profit),
            "commission": float(t.commission),
            "swap": float(t.swap),
            "exit_reason": t.exit_reason.value if hasattr(t.exit_reason, "value") else str(t.exit_reason),
            "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        }
        for t in trades
    ]

    summary["recent_risk_events"] = [
        {
            "id": r.id,
            "signal_id": r.signal_id,
            "event_type": r.event_type.value if hasattr(r.event_type, "value") else str(r.event_type),
            "rule_name": r.rule_name,
            "system_action": r.system_action_taken.value if hasattr(r.system_action_taken, "value") else str(r.system_action_taken),
            "details": r.details,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in risk_events
    ]

    summary["recent_bot_events"] = [
        {
            "id": b.id,
            "category": b.event_category,
            "previous_state": b.previous_state,
            "new_state": b.new_state,
            "triggered_by": b.triggered_by,
            "message": b.message,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bot_events
    ]

    return summary

@router.get("/history/signals")
async def get_signals_history(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(Signal).order_by(desc(Signal.created_at)).limit(limit))
    items = list(res.scalars().all())
    return [
        {
            "id": s.id,
            "signal_uuid": s.signal_uuid,
            "symbol": s.symbol,
            "timeframe": s.timeframe,
            "action": s.action.value,
            "target_price": float(s.target_price) if s.target_price else None,
            "stop_loss": float(s.stop_loss) if s.stop_loss else None,
            "take_profit": float(s.take_profit) if s.take_profit else None,
            "status": s.status.value,
            "rejection_reason": s.rejection_reason,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in items
    ]

@router.get("/history/orders")
async def get_orders_history(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(Order).order_by(desc(Order.submitted_at)).limit(limit))
    items = list(res.scalars().all())
    return [
        {
            "id": o.id,
            "ticket": o.broker_order_ticket,
            "symbol": o.symbol,
            "order_type": o.order_type.value,
            "requested_lots": float(o.requested_lots),
            "filled_lots": float(o.filled_lots),
            "requested_price": float(o.requested_price),
            "execution_price": float(o.execution_price) if o.execution_price else None,
            "status": o.execution_status.value,
            "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
            "filled_at": o.filled_at.isoformat() if o.filled_at else None,
        }
        for o in items
    ]

@router.get("/history/positions")
async def get_positions_history(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(Position).order_by(desc(Position.opened_at)).limit(limit))
    items = list(res.scalars().all())
    return [
        {
            "id": p.id,
            "ticket": p.broker_position_ticket,
            "symbol": p.symbol,
            "side": p.side.value,
            "initial_lots": float(p.initial_lots),
            "current_lots": float(p.current_lots),
            "entry_price": float(p.entry_price),
            "stop_loss": float(p.current_stop_loss) if p.current_stop_loss else None,
            "take_profit": float(p.current_take_profit) if p.current_take_profit else None,
            "status": p.status.value,
            "opened_at": p.opened_at.isoformat() if p.opened_at else None,
            "closed_at": p.closed_at.isoformat() if p.closed_at else None,
        }
        for p in items
    ]

@router.get("/history/trades")
async def get_trades_history(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(Trade).order_by(desc(Trade.closed_at)).limit(limit))
    items = list(res.scalars().all())
    return [
        {
            "id": t.id,
            "position_id": t.position_id,
            "close_price": float(t.close_price),
            "gross_profit": float(t.gross_profit),
            "commission": float(t.commission),
            "swap": float(t.swap),
            "net_profit": float(t.net_profit),
            "pips": float(t.pips),
            "exit_reason": t.exit_reason.value if hasattr(t.exit_reason, "value") else str(t.exit_reason),
            "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        }
        for t in items
    ]

@router.get("/history/risk-events")
async def get_risk_events_history(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(RiskEvent).order_by(desc(RiskEvent.created_at)).limit(limit))
    items = list(res.scalars().all())
    return [
        {
            "id": r.id,
            "signal_id": r.signal_id,
            "event_type": r.event_type.value if hasattr(r.event_type, "value") else str(r.event_type),
            "rule_name": r.rule_name,
            "threshold_value": r.threshold_value,
            "actual_value": r.actual_value,
            "system_action_taken": r.system_action_taken.value if hasattr(r.system_action_taken, "value") else str(r.system_action_taken),
            "details": r.details,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in items
    ]

@router.get("/history/bot-events")
async def get_bot_events_history(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(BotEvent).order_by(desc(BotEvent.created_at)).limit(limit))
    items = list(res.scalars().all())
    return [
        {
            "id": b.id,
            "event_category": b.event_category,
            "previous_state": b.previous_state,
            "new_state": b.new_state,
            "triggered_by": b.triggered_by,
            "message": b.message,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in items
    ]

