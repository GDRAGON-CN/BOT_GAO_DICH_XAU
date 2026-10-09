from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import BotEvent, SystemSetting
from app.repositories.base import BaseRepository

class AuditRepository(BaseRepository[BotEvent]):
    def __init__(self, db: AsyncSession):
        super().__init__(BotEvent, db)

    async def get_recent_events(self, limit: int = 20) -> List[BotEvent]:
        result = await self.db.execute(select(BotEvent).order_by(desc(BotEvent.created_at)).limit(limit))
        return list(result.scalars().all())

    async def get_setting(self, key: str) -> Optional[SystemSetting]:
        result = await self.db.execute(select(SystemSetting).where(SystemSetting.key_name == key))
        return result.scalars().first()
