from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric
from app.database.base import Base

class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    balance = Column(Numeric(14, 2), nullable=False)
    equity = Column(Numeric(14, 2), nullable=False)
    margin = Column(Numeric(14, 2), nullable=False)
    free_margin = Column(Numeric(14, 2), nullable=False)
    margin_level = Column(Numeric(10, 2), nullable=True)
    open_positions_count = Column(Integer, default=0, nullable=False)
    daily_realized_pnl = Column(Numeric(12, 2), default=0.0, nullable=False)
    daily_floating_pnl = Column(Numeric(12, 2), default=0.0, nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
