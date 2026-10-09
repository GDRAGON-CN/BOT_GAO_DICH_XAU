from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from app.core.constants import PositionSide, PositionStatus
from app.database.base import Base

class Position(Base):
    __tablename__ = "positions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    broker_position_ticket = Column(BigInteger, unique=True, nullable=False, index=True)
    opening_order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(PositionSide), nullable=False)
    initial_lots = Column(Numeric(8, 2), nullable=False)
    current_lots = Column(Numeric(8, 2), nullable=False)
    entry_price = Column(Numeric(12, 5), nullable=False)
    current_stop_loss = Column(Numeric(12, 5), nullable=True)
    current_take_profit = Column(Numeric(12, 5), nullable=True)
    trailing_step_points = Column(Numeric(8, 2), nullable=True)
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN, nullable=False, index=True)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    closed_at = Column(DateTime, nullable=True)

    opening_order = relationship("Order", back_populates="position")
    trades = relationship("Trade", back_populates="position")
