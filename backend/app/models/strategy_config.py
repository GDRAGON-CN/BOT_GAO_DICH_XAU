from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text
from app.database.base import Base

class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), unique=True, nullable=False, index=True) # e.g. "XAUUSD_M15_TREND_PULLBACK"
    symbol = Column(String(20), default="XAUUSD", nullable=False, index=True)
    timeframe = Column(String(10), default="M15", nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    risk_percent = Column(Numeric(5, 2), default=1.00, nullable=False)
    max_positions = Column(Integer, default=2, nullable=False)
    max_daily_loss_percent = Column(Numeric(5, 2), default=3.00, nullable=False)
    max_spread_points = Column(Numeric(8, 2), default=35.0, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
