import asyncio
from datetime import datetime
from typing import List, Optional
from loguru import logger
from app.brokers.base import IBrokerAdapter
from app.brokers.symbol_mapper import symbol_mapper
from app.core.config import settings
from app.core.constants import OrderSide, PositionSide
from app.schemas.account import AccountInfoDTO, QuoteDTO, SymbolInfoDTO
from app.schemas.order import OrderExecutionResultDTO, OrderRequestDTO
from app.schemas.position import PositionDTO

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

class MT5BrokerAdapter(IBrokerAdapter):
    """Concrete MT5 adapter executing trades directly on MetaTrader 5 terminal via Win32 IPC."""

    def __init__(self):
        self._connected = False

    async def initialize(self) -> bool:
        if mt5 is None:
            logger.error("MetaTrader5 python library is not available.")
            return False

        def _init_sync():
            kwargs = {}
            if settings.MT5_PATH:
                kwargs["path"] = settings.MT5_PATH
            if settings.MT5_LOGIN and settings.MT5_LOGIN > 0:
                kwargs["login"] = settings.MT5_LOGIN
                kwargs["password"] = settings.MT5_PASSWORD
                kwargs["server"] = settings.MT5_SERVER
                kwargs["timeout"] = settings.MT5_TIMEOUT_MS

            logger.info("Initializing MetaTrader 5 terminal connection...")
            if not mt5.initialize(**kwargs):
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False

            broker_sym = symbol_mapper.to_broker(settings.DEFAULT_SYMBOL)
            mt5.symbol_select(broker_sym, True)
            return True

        self._connected = await asyncio.to_thread(_init_sync)
        if self._connected:
            logger.info("Connected to MetaTrader 5 terminal successfully.")
        return self._connected

    async def shutdown(self) -> None:
        if mt5 and self._connected:
            await asyncio.to_thread(mt5.shutdown)
            self._connected = False
            logger.info("MetaTrader 5 terminal connection closed.")

    async def is_connected(self) -> bool:
        if mt5 is None or not self._connected:
            return False

        def _check():
            info = mt5.terminal_info()
            return info is not None and info.connected

        return await asyncio.to_thread(_check)

    async def get_account_info(self) -> AccountInfoDTO:
        if mt5 is None:
            raise RuntimeError("MT5 library not loaded.")

        def _get():
            info = mt5.account_info()
            if info is None:
                raise RuntimeError(f"Failed to fetch account info: {mt5.last_error()}")
            return AccountInfoDTO(
                login=info.login,
                balance=float(info.balance),
                equity=float(info.equity),
                margin=float(info.margin),
                free_margin=float(info.margin_free),
                margin_level=float(info.margin_level) if info.margin_level is not None else None,
                currency=info.currency,
                server=info.server
            )

        return await asyncio.to_thread(_get)

    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfoDTO]:
        mapped = symbol_mapper.to_broker(symbol)

        def _get():
            info = mt5.symbol_info(mapped)
            if info is None:
                return None
            return SymbolInfoDTO(
                name=mapped,
                point=float(info.point),
                digits=int(info.digits),
                spread_points=float(info.spread),
                bid=float(info.bid),
                ask=float(info.ask),
                lot_min=float(info.volume_min),
                lot_max=float(info.volume_max),
                lot_step=float(info.volume_step),
                trade_contract_size=float(info.trade_contract_size)
            )

        return await asyncio.to_thread(_get)

    async def get_current_quote(self, symbol: str) -> Optional[QuoteDTO]:
        mapped = symbol_mapper.to_broker(symbol)

        def _get():
            tick = mt5.symbol_info_tick(mapped)
            if tick is None:
                return None
            info = mt5.symbol_info(mapped)
            spread = float(info.spread) if info else (tick.ask - tick.bid)
            return QuoteDTO(
                symbol=mapped,
                bid=float(tick.bid),
                ask=float(tick.ask),
                spread_points=spread,
                time=datetime.fromtimestamp(tick.time)
            )

        return await asyncio.to_thread(_get)

    async def execute_market_order(self, request: OrderRequestDTO) -> OrderExecutionResultDTO:
        mapped = symbol_mapper.to_broker(request.symbol)

        def _execute():
            tick = mt5.symbol_info_tick(mapped)
            if tick is None:
                return OrderExecutionResultDTO(
                    success=False,
                    retcode=-1,
                    error_message=f"Current tick unavailable for {mapped}"
                )

            order_type = mt5.ORDER_TYPE_BUY if request.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL
            price = tick.ask if request.side == OrderSide.BUY else tick.bid

            trade_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": mapped,
                "volume": float(request.lots),
                "type": order_type,
                "price": price,
                "deviation": int(request.deviation_points),
                "magic": request.magic,
                "comment": request.comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if request.stop_loss is not None:
                trade_request["sl"] = float(request.stop_loss)
            if request.take_profit is not None:
                trade_request["tp"] = float(request.take_profit)

            logger.info(f"Sending order to MT5: {trade_request}")
            result = mt5.order_send(trade_request)

            if result is None:
                return OrderExecutionResultDTO(
                    success=False,
                    retcode=-2,
                    error_message=f"order_send failed: {mt5.last_error()}"
                )

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return OrderExecutionResultDTO(
                    success=True,
                    retcode=result.retcode,
                    order_ticket=result.order,
                    position_ticket=result.deal,
                    execution_price=float(result.price),
                    lots=float(result.volume),
                    comment=result.comment
                )
            else:
                return OrderExecutionResultDTO(
                    success=False,
                    retcode=result.retcode,
                    error_message=f"Broker rejected: {result.retcode} - {result.comment}"
                )

        return await asyncio.to_thread(_execute)

    async def modify_position(self, ticket: int, sl: Optional[float], tp: Optional[float]) -> OrderExecutionResultDTO:
        def _modify():
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return OrderExecutionResultDTO(success=False, retcode=-1, error_message=f"Position {ticket} not found")

            pos = positions[0]
            req = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": pos.symbol,
                "sl": float(sl) if sl is not None else float(pos.sl),
                "tp": float(tp) if tp is not None else float(pos.tp),
            }
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                return OrderExecutionResultDTO(success=True, retcode=res.retcode, comment="Position modified")
            return OrderExecutionResultDTO(success=False, retcode=res.retcode if res else -1, error_message=res.comment if res else "Failed")

        return await asyncio.to_thread(_modify)

    async def close_position(self, ticket: int, lots: Optional[float] = None) -> OrderExecutionResultDTO:
        def _close():
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return OrderExecutionResultDTO(success=False, retcode=-1, error_message=f"Position {ticket} not found")

            pos = positions[0]
            close_volume = float(lots) if lots is not None else float(pos.volume)
            tick = mt5.symbol_info_tick(pos.symbol)
            if not tick:
                return OrderExecutionResultDTO(success=False, retcode=-1, error_message="No tick to close position")

            order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask

            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": pos.symbol,
                "volume": close_volume,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "comment": "Close by Bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                return OrderExecutionResultDTO(
                    success=True,
                    retcode=res.retcode,
                    order_ticket=res.order,
                    execution_price=float(res.price),
                    lots=close_volume,
                    comment="Position closed"
                )
            return OrderExecutionResultDTO(success=False, retcode=res.retcode if res else -1, error_message=res.comment if res else "Failed to close")

        return await asyncio.to_thread(_close)

    async def get_open_positions(self, symbol: Optional[str] = None) -> List[PositionDTO]:
        mapped = symbol_mapper.to_broker(symbol) if symbol else None

        def _get():
            pos_list = mt5.positions_get(symbol=mapped) if mapped else mt5.positions_get()
            if pos_list is None:
                return []
            results = []
            for p in pos_list:
                results.append(PositionDTO(
                    ticket=p.ticket,
                    symbol=p.symbol,
                    side=PositionSide.LONG if p.type == mt5.POSITION_TYPE_BUY else PositionSide.SHORT,
                    lots=float(p.volume),
                    entry_price=float(p.price_open),
                    current_price=float(p.price_current),
                    profit=float(p.profit),
                    stop_loss=float(p.sl) if p.sl else None,
                    take_profit=float(p.tp) if p.tp else None,
                    magic=p.magic,
                    comment=p.comment,
                    open_time=datetime.fromtimestamp(p.time)
                ))
            return results

        return await asyncio.to_thread(_get)
