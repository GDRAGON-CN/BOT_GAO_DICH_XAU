from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trading_session import TradingSession
from app.models.strategy_config import StrategyConfig
from app.repositories.base import BaseRepository

class TradingSessionRepository(BaseRepository[TradingSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(TradingSession, db)

    async def get_by_name(self, session_name: str) -> Optional[TradingSession]:
        stmt = select(TradingSession).where(TradingSession.session_name == session_name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_active_sessions(self) -> List[TradingSession]:
        stmt = select(TradingSession).where(TradingSession.is_active == True)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class StrategyConfigRepository(BaseRepository[StrategyConfig]):
    def __init__(self, db: AsyncSession):
        super().__init__(StrategyConfig, db)

    async def get_by_name(self, strategy_name: str) -> Optional[StrategyConfig]:
        stmt = select(StrategyConfig).where(StrategyConfig.strategy_name == strategy_name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_symbol(self, symbol: str) -> List[StrategyConfig]:
        stmt = select(StrategyConfig).where(
            StrategyConfig.symbol == symbol,
            StrategyConfig.is_enabled == True
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
