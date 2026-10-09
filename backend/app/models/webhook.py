from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, JSON, String, Integer
from sqlalchemy.orm import relationship
from app.core.constants import WebhookStatus
from app.database.base import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)

    event_uuid = Column(String(36), unique=True, nullable=False, index=True)
    payload_hash = Column(String(64), nullable=False, index=True)
    source_ip = Column(String(45), nullable=True)
    raw_payload = Column(JSON, nullable=False)
    processing_status = Column(Enum(WebhookStatus), default=WebhookStatus.RECEIVED, nullable=False, index=True)
    rejection_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    signals = relationship("Signal", back_populates="webhook_event")
