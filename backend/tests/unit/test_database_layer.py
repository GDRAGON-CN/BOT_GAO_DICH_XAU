"""Database schema, models, constraints, and transactions tests using synchronous engine."""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.core.constants import OrderSide, OrderStatus, SignalStatus
from app.models.signal import Signal
from app.models.order import Order
from app.models.position import Position
from app.models.trade import Trade
from app.models.webhook import WebhookEvent

@pytest.fixture
def sync_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

def test_database_insert_and_select(sync_db):
    """Test standard entity insertion and retrieval."""
    sig = Signal(
        signal_uuid="sig-test-123",
        symbol="XAUUSD",
        timeframe="M15",
        action=OrderSide.BUY,
        target_price=Decimal("2650.00"),
        stop_loss=Decimal("2645.00"),
        take_profit=Decimal("2660.00"),
        status=SignalStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )
    sync_db.add(sig)
    sync_db.commit()

    retrieved = sync_db.query(Signal).filter_by(signal_uuid="sig-test-123").first()
    assert retrieved is not None
    assert retrieved.symbol == "XAUUSD"
    assert retrieved.action == OrderSide.BUY
    assert float(retrieved.stop_loss) == 2645.00

def test_database_update(sync_db):
    """Test entity state update and persistence."""
    sig = Signal(
        signal_uuid="sig-update-456",
        symbol="XAUUSD",
        timeframe="M15",
        action=OrderSide.BUY,
        stop_loss=Decimal("2645.00"),
        status=SignalStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )
    sync_db.add(sig)
    sync_db.commit()

    sig.status = SignalStatus.EXECUTED
    sig.rejection_reason = "Executed successfully"
    sync_db.commit()

    updated = sync_db.query(Signal).filter_by(signal_uuid="sig-update-456").first()
    assert updated.status == SignalStatus.EXECUTED
    assert updated.rejection_reason == "Executed successfully"

def test_database_transaction_rollback(sync_db):
    """Test that transaction rollback prevents partial or dirty state writes."""
    sig = Signal(
        signal_uuid="sig-rollback-789",
        symbol="XAUUSD",
        timeframe="M15",
        action=OrderSide.SELL,
        stop_loss=Decimal("2655.00"),
        status=SignalStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )
    sync_db.add(sig)
    sync_db.flush()

    # Explicitly rollback before committing
    sync_db.rollback()

    assert sync_db.query(Signal).filter_by(signal_uuid="sig-rollback-789").first() is None

def test_database_unique_constraints(sync_db):
    """Test that duplicate unique fields violate constraints and raise IntegrityError."""
    evt1 = WebhookEvent(
        event_uuid="dup-uuid-1",
        payload_hash="hash-123",
        source_ip="127.0.0.1",
        raw_payload={"foo": "bar"}
    )
    sync_db.add(evt1)
    sync_db.commit()

    evt2 = WebhookEvent(
        event_uuid="dup-uuid-1",  # Same unique UUID
        payload_hash="hash-456",
        source_ip="127.0.0.1",
        raw_payload={"foo": "bar"}
    )
    sync_db.add(evt2)
    with pytest.raises(IntegrityError):
        sync_db.commit()
    sync_db.rollback()
