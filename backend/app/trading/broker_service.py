"""Broker management and abstraction service."""
from typing import List, Optional
from loguru import logger
# pyrefly: ignore [missing-import]
from app.brokers.base import IBrokerAdapter
# pyrefly: ignore [missing-import]
from app.schemas.account import AccountInfoDTO, QuoteDTO, SymbolInfoDTO
# pyrefly: ignore [missing-import]
from app.schemas.order import OrderExecutionResultDTO, OrderRequestDTO
# pyrefly: ignore [missing-import]
from app.schemas.position import PositionDTO

class BrokerService:
    """Wraps broker interactions with connection verification and logging."""

    def __init__(self, broker: IBrokerAdapter):
        self.broker = broker

    async def ensure_connected(self) -> bool:
        """Verifies if broker is active and connected."""
        connected = await self.broker.is_connected()
        if not connected:
            logger.error("Broker adapter is disconnected from MT5 terminal.")
        return connected

    async def get_account_info(self) -> AccountInfoDTO:
        return await self.broker.get_account_info()

    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfoDTO]:
        return await self.broker.get_symbol_info(symbol)

    async def get_current_quote(self, symbol: str) -> Optional[QuoteDTO]:
        return await self.broker.get_current_quote(symbol)

    async def execute_market_order(self, request: OrderRequestDTO) -> OrderExecutionResultDTO:
        return await self.broker.execute_market_order(request)

    async def modify_position(self, ticket: int, sl: Optional[float], tp: Optional[float]) -> OrderExecutionResultDTO:
        return await self.broker.modify_position(ticket, sl, tp)

    async def close_position(self, ticket: int, lots: Optional[float] = None) -> OrderExecutionResultDTO:
        return await self.broker.close_position(ticket, lots)

    async def get_open_positions(self, symbol: Optional[str] = None) -> List[PositionDTO]:
        return await self.broker.get_open_positions(symbol)
