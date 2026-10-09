from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AccountInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: Optional[float] = None
    currency: str = "USD"
    server: str = ""

class SymbolInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    point: float
    digits: int
    spread_points: float
    bid: float
    ask: float
    lot_min: float
    lot_max: float
    lot_step: float
    trade_contract_size: float
    tick_size: Optional[float] = None
    tick_value: Optional[float] = None

class QuoteDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    bid: float
    ask: float
    spread_points: float
    time: datetime
