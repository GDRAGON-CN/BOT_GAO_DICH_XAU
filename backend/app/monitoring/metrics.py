from typing import Any, Dict
from app.brokers.base import IBrokerAdapter
from app.repositories.order_repo import OrderRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.signal_repo import SignalRepository

class MetricsAggregator:
    """Aggregates account balances, recent signals, and open positions for UI telemetry."""

    def __init__(
        self,
        broker: IBrokerAdapter,
        signal_repo: SignalRepository,
        order_repo: OrderRepository,
        position_repo: PositionRepository
    ):
        self.broker = broker
        self.signal_repo = signal_repo
        self.order_repo = order_repo
        self.position_repo = position_repo

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        account = await self.broker.get_account_info()
        positions = await self.broker.get_open_positions()
        recent_signals = await self.signal_repo.get_recent(limit=10)
        recent_orders = await self.order_repo.get_recent(limit=10)

        return {
            "account": account.model_dump(),
            "open_positions": [p.model_dump() for p in positions],
            "recent_signals": [
                {
                    "id": s.id,
                    "uuid": s.signal_uuid[:8],
                    "symbol": s.symbol,
                    "action": s.action.value,
                    "status": s.status.value,
                    "rejection_reason": s.rejection_reason,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in recent_signals
            ],
            "recent_orders": [
                {
                    "id": o.id,
                    "ticket": o.broker_order_ticket,
                    "symbol": o.symbol,
                    "type": o.order_type.value,
                    "lots": float(o.filled_lots),
                    "price": float(o.execution_price or 0.0),
                    "status": o.execution_status.value,
                    "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
                }
                for o in recent_orders
            ]
        }
