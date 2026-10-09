from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import PositionStatus
from app.models.position import Position
from app.repositories.base import BaseRepository

class PositionRepository(BaseRepository[Position]):
    def __init__(self, db: AsyncSession):
        super().__init__(Position, db)

    async def get_by_ticket(self, ticket: int) -> Optional[Position]:
        result = await self.db.execute(select(Position).where(Position.broker_position_ticket == ticket))
        return result.scalars().first()

    async def get_open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        query = select(Position).where(Position.status == PositionStatus.OPEN)
        if symbol:
            query = query.where(Position.symbol == symbol)
        result = await self.db.execute(query)
        return list(result.scalars().all())
