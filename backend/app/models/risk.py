from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
# pyrefly: ignore [missing-import]
from app.core.constants import RiskAction, RiskEventType
# pyrefly: ignore [missing-import]
from app.database.base import Base

class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(BigInteger, ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(Enum(RiskEventType), nullable=False)
    rule_name = Column(String(100), nullable=False)
    threshold_value = Column(String(50), nullable=False)
    actual_value = Column(String(50), nullable=False)
    system_action_taken = Column(Enum(RiskAction), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    signal = relationship("Signal", back_populates="risk_events")
