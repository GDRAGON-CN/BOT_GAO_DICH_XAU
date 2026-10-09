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

    async def get_daily_realized_loss(self, since_utc: Optional[datetime] = None) -> float:
        """
        Calculates today's cumulative realized loss in monetary terms (USD).
        Sums all closed trades where net_profit < 0 starting from midnight UTC today (or since_utc).
        Returns a positive float representing total dollars lost today (e.g. $150.00).
        """
        if since_utc is None:
            now = datetime.now(timezone.utc)
            since_utc = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

        # Filter closed trades since beginning of UTC day
        stmt = select(func.sum(Trade.net_profit)).where(
            Trade.closed_at >= since_utc.replace(tzinfo=None),
            Trade.net_profit < 0
        )
        result = await self.db.execute(stmt)
        total_loss = result.scalar()
        if total_loss is None:
            return 0.0
        return abs(float(total_loss))
