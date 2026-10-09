from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from app.core.constants import OrderSide, OrderStatus
from app.database.base import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(BigInteger, ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)
    broker_order_ticket = Column(BigInteger, unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    order_type = Column(Enum(OrderSide), nullable=False)
    requested_lots = Column(Numeric(8, 2), nullable=False)
    filled_lots = Column(Numeric(8, 2), default=0.0, nullable=False)
    requested_price = Column(Numeric(12, 5), nullable=False)
    execution_price = Column(Numeric(12, 5), nullable=True)
    slippage_points = Column(Numeric(8, 2), default=0.0, nullable=False)
    stop_loss = Column(Numeric(12, 5), nullable=True)
    take_profit = Column(Numeric(12, 5), nullable=True)
    execution_retcode = Column(Integer, nullable=True)
    execution_status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    filled_at = Column(DateTime, nullable=True)

    signal = relationship("Signal", back_populates="orders")
    position = relationship("Position", back_populates="opening_order", uselist=False)
