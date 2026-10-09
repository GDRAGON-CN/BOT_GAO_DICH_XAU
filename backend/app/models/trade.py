from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.constants import ExitReason
from app.database.base import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    position_id = Column(BigInteger, ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    closing_order_ticket = Column(BigInteger, nullable=False, index=True)
    close_price = Column(Numeric(12, 5), nullable=False)
    gross_profit = Column(Numeric(12, 2), nullable=False)
    commission = Column(Numeric(10, 2), default=0.0, nullable=False)
    swap = Column(Numeric(10, 2), default=0.0, nullable=False)
    net_profit = Column(Numeric(12, 2), nullable=False)
    pips = Column(Numeric(10, 1), default=0.0, nullable=False)
    exit_reason = Column(Enum(ExitReason), nullable=False)
    closed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    position = relationship("Position", back_populates="trades")
