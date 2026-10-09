from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
from app.brokers.base import IBrokerAdapter
from app.core.constants import OrderSide, PositionSide
from app.schemas.account import AccountInfoDTO, QuoteDTO, SymbolInfoDTO
from app.schemas.order import OrderExecutionResultDTO, OrderRequestDTO
from app.schemas.position import PositionDTO

class MockBrokerAdapter(IBrokerAdapter):
    """Simulates broker execution for automated unit testing and sandbox operations."""

    def __init__(self):
        self._connected = True
        self._balance = 10000.0
        self._ticket_counter = 100000
        self._positions: Dict[int, PositionDTO] = {}
        self._prices = {
            "XAUUSD": {"bid": 2650.50, "ask": 2650.70, "spread": 20.0}
        }

    async def initialize(self) -> bool:
        logger.info("[MockBroker] Initialized.")
        self._connected = True
        return True

    async def shutdown(self) -> None:
        logger.info("[MockBroker] Shutdown.")
        self._connected = False

    async def is_connected(self) -> bool:
        return self._connected

    async def get_account_info(self) -> AccountInfoDTO:
        floating_pnl = sum(p.profit for p in self._positions.values())
        return AccountInfoDTO(
            login=99999999,
            balance=self._balance,
            equity=self._balance + floating_pnl,
            margin=len(self._positions) * 200.0,
            free_margin=self._balance - (len(self._positions) * 200.0),
            margin_level=1000.0,
            currency="USD",
            server="MockBroker-Sandbox"
        )

    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfoDTO]:
        sym = symbol.upper()
        p = self._prices.get(sym, {"bid": 2650.50, "ask": 2650.70, "spread": 20.0})
        return SymbolInfoDTO(
            name=sym,
            point=0.01,
            digits=2,
            spread_points=p["spread"],
            bid=p["bid"],
            ask=p["ask"],
            lot_min=0.01,
            lot_max=50.0,
            lot_step=0.01,
            trade_contract_size=100.0
        )

    async def get_current_quote(self, symbol: str) -> Optional[QuoteDTO]:
        sym = symbol.upper()
        p = self._prices.get(sym, {"bid": 2650.50, "ask": 2650.70, "spread": 20.0})
        return QuoteDTO(
            symbol=sym,
            bid=p["bid"],
            ask=p["ask"],
            spread_points=p["spread"],
            time=datetime.utcnow()
        )

    async def execute_market_order(self, request: OrderRequestDTO) -> OrderExecutionResultDTO:
        self._ticket_counter += 1
        ticket = self._ticket_counter
        p = self._prices.get(request.symbol.upper(), {"bid": 2650.50, "ask": 2650.70})
        exec_price = p["ask"] if request.side == OrderSide.BUY else p["bid"]

        pos = PositionDTO(
            ticket=ticket,
            symbol=request.symbol.upper(),
            side=PositionSide.LONG if request.side == OrderSide.BUY else PositionSide.SHORT,
            lots=request.lots,
            entry_price=exec_price,
            current_price=exec_price,
            profit=0.0,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            magic=request.magic,
            comment=request.comment,
            open_time=datetime.utcnow()
        )
        self._positions[ticket] = pos

        logger.info(f"[MockBroker] Executed order #{ticket} {request.side} {request.lots} lots @ {exec_price}")
        return OrderExecutionResultDTO(
            success=True,
            retcode=10009,
            order_ticket=ticket,
            position_ticket=ticket,
            execution_price=exec_price,
            lots=request.lots,
            comment="Filled by MockBroker"
        )

    async def modify_position(self, ticket: int, sl: Optional[float], tp: Optional[float]) -> OrderExecutionResultDTO:
        if ticket in self._positions:
            self._positions[ticket].stop_loss = sl
            self._positions[ticket].take_profit = tp
            return OrderExecutionResultDTO(success=True, retcode=10009, comment="Modified in MockBroker")
        return OrderExecutionResultDTO(success=False, retcode=-1, error_message="Position not found")

    async def close_position(self, ticket: int, lots: Optional[float] = None) -> OrderExecutionResultDTO:
        if ticket in self._positions:
            pos = self._positions.pop(ticket)
            self._balance += pos.profit
            return OrderExecutionResultDTO(
                success=True,
                retcode=10009,
                order_ticket=ticket + 500,
                execution_price=pos.current_price,
                lots=pos.lots,
                comment="Closed by MockBroker"
            )
        return OrderExecutionResultDTO(success=False, retcode=-1, error_message="Position not found")

    async def get_open_positions(self, symbol: Optional[str] = None) -> List[PositionDTO]:
        if symbol:
            return [p for p in self._positions.values() if p.symbol == symbol.upper()]
        return list(self._positions.values())
