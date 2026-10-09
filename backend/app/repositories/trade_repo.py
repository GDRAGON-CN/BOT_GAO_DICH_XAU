from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trade import Trade
from app.repositories.base import BaseRepository

class TradeRepository(BaseRepository[Trade]):
    def __init__(self, db: AsyncSession):
        super().__init__(Trade, db)

    async def get_recent(self, limit: int = 20) -> List[Trade]:
        result = await self.db.execute(select(Trade).order_by(desc(Trade.closed_at)).limit(limit))
        return list(result.scalars().all())

    async def get_daily_realized_loss(
        self,
        since_utc: Optional[datetime] = None,
        net_of_profits: bool = False
    ) -> float:
        """
        Calculates today's cumulative realized loss in monetary terms (USD).
        Trading-day reset boundary: Midnight 00:00:00 UTC (matching global Forex/XAUUSD rollover conventions).
        
        Note on Commission & Swaps:
        Trade.net_profit in the database is defined as:
            net_profit = gross_profit + commission + swap
        where commission and swap are negative or zero, fully accounting for broker transaction costs.
        
        Modes:
        - net_of_profits=False (Default / Strict Circuit Breaker):
          Sums ONLY losing closed trades (where net_profit < 0). This prevents a morning winning trade
          from artificially masking an afternoon string of severe losses.
        - net_of_profits=True (Daily Balance Drawdown mode):
          Sums all trades (wins + losses). If net PnL is negative, returns positive loss amount.
        """
        if since_utc is None:
            now = datetime.now(timezone.utc)
            # Strict UTC trading day boundary at 00:00:00
            since_utc = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

        if net_of_profits:
            stmt = select(func.sum(Trade.net_profit)).where(
                Trade.closed_at >= since_utc.replace(tzinfo=None)
            )
            result = await self.db.execute(stmt)
            total = result.scalar()
            if total is None or float(total) >= 0.0:
                return 0.0
            return abs(float(total))

        # Strict conservative loss accumulator: sum only losing trades
        stmt = select(func.sum(Trade.net_profit)).where(
            Trade.closed_at >= since_utc.replace(tzinfo=None),
            Trade.net_profit < 0
        )
        result = await self.db.execute(stmt)
        total_loss = result.scalar()
        if total_loss is None:
            return 0.0
        return abs(float(total_loss))

    async def get_daily_net_pnl(self, since_utc: Optional[datetime] = None) -> float:
        """Calculates today's total net realized PnL (positive for profit, negative for loss)."""
        if since_utc is None:
            now = datetime.now(timezone.utc)
            since_utc = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

        stmt = select(func.sum(Trade.net_profit)).where(
            Trade.closed_at >= since_utc.replace(tzinfo=None)
        )
        result = await self.db.execute(stmt)
        total = result.scalar()
        return float(total) if total is not None else 0.0

