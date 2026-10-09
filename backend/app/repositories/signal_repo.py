from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.signal import Signal
from app.repositories.base import BaseRepository

class SignalRepository(BaseRepository[Signal]):
    def __init__(self, db: AsyncSession):
        super().__init__(Signal, db)

    async def get_by_uuid(self, signal_uuid: str) -> Optional[Signal]:
        result = await self.db.execute(select(Signal).where(Signal.signal_uuid == signal_uuid))
        return result.scalars().first()

    async def get_recent(self, limit: int = 10) -> List[Signal]:
        result = await self.db.execute(select(Signal).order_by(desc(Signal.created_at)).limit(limit))
        return list(result.scalars().all())
