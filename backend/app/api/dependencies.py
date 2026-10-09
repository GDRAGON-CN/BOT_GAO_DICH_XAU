from sqlalchemy.ext.asyncio import AsyncSession
from app.brokers.base import IBrokerAdapter
from app.brokers.mock_broker import MockBrokerAdapter
from app.brokers.mt5_broker import MT5BrokerAdapter
from app.core.config import settings
from app.database.session import get_db_session
from app.repositories.order_repo import OrderRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.signal_repo import SignalRepository
from app.repositories.webhook_repo import WebhookRepository

_broker_instance: IBrokerAdapter = None

def get_broker() -> IBrokerAdapter:
    global _broker_instance
    if _broker_instance is None:
        if settings.MT5_LOGIN == 0:
            _broker_instance = MockBrokerAdapter()
        else:
            _broker_instance = MT5BrokerAdapter()
    return _broker_instance

def set_broker(broker: IBrokerAdapter):
    global _broker_instance
    _broker_instance = broker

def get_signal_repo(db: AsyncSession) -> SignalRepository:
    return SignalRepository(db)

def get_order_repo(db: AsyncSession) -> OrderRepository:
    return OrderRepository(db)

def get_position_repo(db: AsyncSession) -> PositionRepository:
    return PositionRepository(db)

def get_webhook_repo(db: AsyncSession) -> WebhookRepository:
    return WebhookRepository(db)
