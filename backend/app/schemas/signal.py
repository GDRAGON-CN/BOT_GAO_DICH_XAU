from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
# pyrefly: ignore [missing-import]
from app.core.constants import OrderSide, SignalStatus

class SignalDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    signal_uuid: str
    symbol: str
    timeframe: str
    action: OrderSide
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: str = "DEFAULT"
    source: str = "TradingView"
    webhook_event_id: Optional[int] = None
    timestamp: datetime = datetime.utcnow()
    status: SignalStatus = SignalStatus.PENDING
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
