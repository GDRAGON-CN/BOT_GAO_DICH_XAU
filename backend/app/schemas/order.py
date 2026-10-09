from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
# pyrefly: ignore [missing-import]
from app.core.constants import OrderSide, OrderStatus

class OrderRequestDTO(BaseModel):
    symbol: str
    side: OrderSide
    lots: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    deviation_points: float = 20.0
    magic: int = 123456
    comment: str = "GoldBot"

class OrderExecutionResultDTO(BaseModel):
    success: bool
    retcode: int
    order_ticket: Optional[int] = None
    position_ticket: Optional[int] = None
    execution_price: Optional[float] = None
    lots: Optional[float] = None
    comment: Optional[str] = None
    error_message: Optional[str] = None

class OrderDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    broker_order_ticket: int
    symbol: str
    order_type: OrderSide
    requested_lots: float
    filled_lots: float
    requested_price: float
    execution_price: Optional[float] = None
    execution_status: OrderStatus
    submitted_at: Optional[datetime] = None
