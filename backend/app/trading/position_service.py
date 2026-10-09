"""Position validation and lifecycle tracking service."""
from typing import List, Optional
from loguru import logger
# pyrefly: ignore [missing-import]
from app.brokers.base import IBrokerAdapter
# pyrefly: ignore [missing-import]
from app.schemas.order import OrderExecutionResultDTO
# pyrefly: ignore [missing-import]
from app.schemas.position import PositionDTO

class PositionService:
    """Manages active broker positions, concurrency validation, and bulk closures."""

    def __init__(self, broker: IBrokerAdapter):
        self.broker = broker

    async def get_active_positions(self, symbol: Optional[str] = None) -> List[PositionDTO]:
        return await self.broker.get_open_positions(symbol)

    async def validate_position_limit(self, max_positions: int, symbol: Optional[str] = None) -> bool:
        positions = await self.get_active_positions(symbol)
        return len(positions) < max_positions

    async def close_position(self, ticket: int, lots: Optional[float] = None) -> OrderExecutionResultDTO:
        logger.info(f"Closing position ticket #{ticket}")
        res = await self.broker.close_position(ticket, lots)
        if res.success:
            # pyrefly: ignore [missing-import]
            from app.notifications.telegram_bot import telegram_bot
            profit = float(res.profit) if res.profit is not None else 0.0
            telegram_bot.notify_position_closed(
                ticket=ticket,
                symbol="XAUUSD",
                close_price=float(res.execution_price) if res.execution_price else 0.0,
                profit=profit,
                reason="CLOSE_COMMAND"
            )
            if profit > 0:
                telegram_bot.notify_profit(trade_id=ticket, symbol="XAUUSD", profit=profit)
            elif profit < 0:
                telegram_bot.notify_loss(trade_id=ticket, symbol="XAUUSD", loss=profit)
        return res


    async def update_stops(self, ticket: int, sl: Optional[float], tp: Optional[float]) -> OrderExecutionResultDTO:
        logger.info(f"Modifying stops for position #{ticket}: SL={sl}, TP={tp}")
        return await self.broker.modify_position(ticket, sl, tp)

    async def close_all_positions(self, symbol: Optional[str] = None) -> List[OrderExecutionResultDTO]:
        positions = await self.get_active_positions(symbol)
        results = []
        for pos in positions:
            res = await self.close_position(pos.ticket)
            results.append(res)
        return results
