from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.account import AccountInfoDTO, QuoteDTO, SymbolInfoDTO
from app.schemas.order import OrderExecutionResultDTO, OrderRequestDTO
from app.schemas.position import PositionDTO

class IBrokerAdapter(ABC):
    """Abstract broker interface."""

    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        pass

    @abstractmethod
    async def get_account_info(self) -> AccountInfoDTO:
        pass

    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfoDTO]:
        pass

    @abstractmethod
    async def get_current_quote(self, symbol: str) -> Optional[QuoteDTO]:
        pass

    @abstractmethod
    async def execute_market_order(self, request: OrderRequestDTO) -> OrderExecutionResultDTO:
        pass

    @abstractmethod
    async def modify_position(self, ticket: int, sl: Optional[float], tp: Optional[float]) -> OrderExecutionResultDTO:
        pass

    @abstractmethod
    async def close_position(self, ticket: int, lots: Optional[float] = None) -> OrderExecutionResultDTO:
        pass

    @abstractmethod
    async def get_open_positions(self, symbol: Optional[str] = None) -> List[PositionDTO]:
        pass
