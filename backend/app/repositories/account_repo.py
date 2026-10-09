from typing import Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.account import AccountSnapshot
from app.repositories.base import BaseRepository

class AccountRepository(BaseRepository[AccountSnapshot]):
    def __init__(self, db: AsyncSession):
        super().__init__(AccountSnapshot, db)

    async def get_latest(self) -> Optional[AccountSnapshot]:
        result = await self.db.execute(select(AccountSnapshot).order_by(desc(AccountSnapshot.captured_at)).limit(1))
        return result.scalars().first()
