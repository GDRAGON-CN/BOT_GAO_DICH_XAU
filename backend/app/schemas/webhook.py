from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, model_validator
from app.core.constants import OrderSide

class TradingViewWebhookSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: Optional[str] = None
    symbol: str
    action: OrderSide
    timeframe: str = "M15"
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    risk_percent: Optional[float] = 1.0
    strategy: Optional[str] = "gold_m15_v1"
    strategy_name: Optional[str] = None
    timestamp: Optional[str] = None
    bar_time: Optional[str] = None
    secret: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def normalize_fields(self):
        # Normalize entry and price
        if self.entry is not None and self.price is None:
            self.price = self.entry
        elif self.price is not None and self.entry is None:
            self.entry = self.price

        # Normalize stop loss
        if self.stop_loss is not None and self.sl is None:
            self.sl = self.stop_loss
        elif self.sl is not None and self.stop_loss is None:
            self.stop_loss = self.sl

        # Normalize take profit
        if self.take_profit is not None and self.tp is None:
            self.tp = self.take_profit
        elif self.tp is not None and self.take_profit is None:
            self.take_profit = self.tp

        # Normalize strategy name
        if self.strategy is not None and self.strategy_name is None:
            self.strategy_name = self.strategy
        elif self.strategy_name is not None and self.strategy is None:
            self.strategy = self.strategy_name

        # Normalize bar_time and timestamp
        if self.timestamp is not None and self.bar_time is None:
            self.bar_time = self.timestamp
        elif self.bar_time is not None and self.timestamp is None:
            self.timestamp = self.bar_time

        return self
