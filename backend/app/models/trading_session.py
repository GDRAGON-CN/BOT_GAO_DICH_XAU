from datetime import datetime, time
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Integer, Numeric, String, Time
from app.database.base import Base

class TradingSession(Base):
    __tablename__ = "trading_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_name = Column(String(50), unique=True, nullable=False, index=True) # e.g. "LONDON", "NEW_YORK", "ASIAN"
    is_active = Column(Boolean, default=True, nullable=False)
    start_time_utc = Column(Time, nullable=False) # e.g. 07:00:00
    end_time_utc = Column(Time, nullable=False)   # e.g. 16:00:00
    max_allowed_spread_points = Column(Numeric(8, 2), default=35.0, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
