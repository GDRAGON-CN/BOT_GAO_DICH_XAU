from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, JSON, String, Text
from app.database.base import Base

class BotEvent(Base):
    __tablename__ = "bot_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_category = Column(String(50), nullable=False, index=True)
    previous_state = Column(String(30), nullable=True)
    new_state = Column(String(30), nullable=True)
    triggered_by = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key_name = Column(String(100), primary_key=True)
    config_value = Column(JSON, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
