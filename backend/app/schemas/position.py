from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.core.constants import PositionSide, PositionStatus

class PositionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket: int
    symbol: str
    side: PositionSide
    lots: float
    entry_price: float
    current_price: float
    profit: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    magic: int = 123456
    comment: str = ""
    open_time: Optional[datetime] = None
