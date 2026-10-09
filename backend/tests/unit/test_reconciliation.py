"""Unit tests for MT5 State Reconciliation Service."""
import pytest
from datetime import datetime
from app.brokers.mock_broker import MockBrokerAdapter
from app.core.constants import PositionSide, PositionStatus
from app.models.account import AccountSnapshot
from app.models.audit import BotEvent
from app.models.position import Position
from app.schemas.position import PositionDTO
from app.trading.reconciliation_service import ReconciliationService

class MockReconciliationDB:
    def __init__(self, initial_positions=None):
        self.positions = initial_positions or []
        self.added = []
        self.committed = False

    def add(self, entity):
        self.added.append(entity)

    async def execute(self, stmt):
        class Result:
            def __init__(self, data):
                self._data = data
            def scalars(self):
                return self
            def all(self):
                return self._data
        return Result(self.positions)

    async def commit(self):
        self.committed = True

@pytest.mark.asyncio
async def test_reconciliation_detects_closed_positions_on_broker(mock_broker):
    """
    Case A: DB has position OPEN (ticket #12345), but MT5 has no positions open
    (e.g. Stop Loss hit while bot backend was restarting/offline).
    Reconciliation must mark DB position as CLOSED and record BotEvent audit.
    """
    db_pos = Position(
        id=1,
        broker_position_ticket=12345,
        symbol="XAUUSD",
        side=PositionSide.LONG,
        status=PositionStatus.OPEN
    )
    mock_db = MockReconciliationDB(initial_positions=[db_pos])

    # Broker has NO open positions
    mock_broker._positions = {}

    reconciler = ReconciliationService(mock_broker)
    report = await reconciler.run_reconciliation(mock_db)

    assert report["broker_connected"] is True
    assert report["orphaned_db_positions_closed"] == 1
    assert db_pos.status == PositionStatus.CLOSED
    assert db_pos.closed_at is not None

    # Check that audit event was added
    audit_events = [e for e in mock_db.added if isinstance(e, BotEvent)]
    assert len(audit_events) >= 1
    assert "Ticket #12345" in audit_events[0].message

@pytest.mark.asyncio
async def test_reconciliation_detects_untracked_broker_position(mock_broker):
    """
    Case B: MT5 has an open position (ticket #88888), but DB does not know about it.
    Reconciliation must detect it, log an audit event, and report it.
    """
    mock_db = MockReconciliationDB(initial_positions=[])

    # Broker HAS an open position
    mock_broker._positions = {
        88888: PositionDTO(
            ticket=88888,
            symbol="XAUUSD",
            side=PositionSide.SHORT,
            lots=0.10,
            entry_price=2650.0,
            current_price=2650.0,
            profit=0.0,
            open_time=datetime.utcnow()
        )
    }

    reconciler = ReconciliationService(mock_broker)
    report = await reconciler.run_reconciliation(mock_db)

    assert report["untracked_broker_positions_imported"] == 1
    audit_events = [e for e in mock_db.added if isinstance(e, BotEvent)]
    assert any("88888" in e.message for e in audit_events)
