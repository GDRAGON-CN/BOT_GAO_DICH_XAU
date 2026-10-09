from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook import WebhookEvent
from app.repositories.base import BaseRepository

class WebhookRepository(BaseRepository[WebhookEvent]):
    def __init__(self, db: AsyncSession):
        super().__init__(WebhookEvent, db)

    async def get_by_hash(self, payload_hash: str) -> Optional[WebhookEvent]:
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.payload_hash == payload_hash)
        )
        return result.scalars().first()
