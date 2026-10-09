from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order
from app.repositories.base import BaseRepository

class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)

    async def get_by_ticket(self, ticket: int) -> Optional[Order]:
        result = await self.db.execute(select(Order).where(Order.broker_order_ticket == ticket))
        return result.scalars().first()

    async def get_recent(self, limit: int = 15) -> List[Order]:
        result = await self.db.execute(select(Order).order_by(desc(Order.submitted_at)).limit(limit))
        return list(result.scalars().all())
