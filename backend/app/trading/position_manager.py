from typing import List, Optional
from loguru import logger
from app.brokers.base import IBrokerAdapter
from app.schemas.order import OrderExecutionResultDTO
from app.schemas.position import PositionDTO

class PositionManager:
    """Manages tracking, reconciliation, and modification of active broker positions."""

    def __init__(self, broker: IBrokerAdapter):
        self.broker = broker

    async def get_active_positions(self, symbol: Optional[str] = None) -> List[PositionDTO]:
        return await self.broker.get_open_positions(symbol)

    async def close_position(self, ticket: int, lots: Optional[float] = None) -> OrderExecutionResultDTO:
        logger.info(f"Closing position ticket #{ticket}")
        return await self.broker.close_position(ticket, lots)

    async def update_stops(self, ticket: int, sl: Optional[float], tp: Optional[float]) -> OrderExecutionResultDTO:
        logger.info(f"Modifying stops for position ticket #{ticket}: SL={sl}, TP={tp}")
        return await self.broker.modify_position(ticket, sl, tp)

    async def close_all_positions(self, symbol: Optional[str] = None) -> List[OrderExecutionResultDTO]:
        positions = await self.get_active_positions(symbol)
        results = []
        for pos in positions:
            res = await self.close_position(pos.ticket)
            results.append(res)
        return results
