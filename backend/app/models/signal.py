from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Numeric, String, Integer
from sqlalchemy.orm import relationship
from app.core.constants import OrderSide, SignalStatus
from app.database.base import Base

class Signal(Base):
    __tablename__ = "signals"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)

    webhook_event_id = Column(BigInteger, ForeignKey("webhook_events.id", ondelete="SET NULL"), nullable=True)
    signal_uuid = Column(String(36), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), default="M15", nullable=False)
    action = Column(Enum(OrderSide), nullable=False)
    target_price = Column(Numeric(12, 5), nullable=True)
    stop_loss = Column(Numeric(12, 5), nullable=True)
    take_profit = Column(Numeric(12, 5), nullable=True)
    status = Column(Enum(SignalStatus), default=SignalStatus.PENDING, nullable=False, index=True)
    rejection_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    webhook_event = relationship("WebhookEvent", back_populates="signals")
    orders = relationship("Order", back_populates="signal")
    risk_events = relationship("RiskEvent", back_populates="signal")
