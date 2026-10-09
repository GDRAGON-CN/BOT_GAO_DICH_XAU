from typing import List
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trade import Trade
from app.repositories.base import BaseRepository

class TradeRepository(BaseRepository[Trade]):
    def __init__(self, db: AsyncSession):
        super().__init__(Trade, db)

    async def get_recent(self, limit: int = 20) -> List[Trade]:
        result = await self.db.execute(select(Trade).order_by(desc(Trade.closed_at)).limit(limit))
        return list(result.scalars().all())
