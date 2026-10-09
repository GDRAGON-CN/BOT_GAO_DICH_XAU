"""Comprehensive unit and integration test suite for the complete trading engine pipeline."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, time
# pyrefly: ignore [missing-import]
from app.brokers.mock_broker import MockBrokerAdapter
# pyrefly: ignore [missing-import]
from app.core.constants import OrderSide, OrderStatus, SignalStatus
# pyrefly: ignore [missing-import]
from app.models.signal import Signal
# pyrefly: ignore [missing-import]
from app.schemas.order import OrderExecutionResultDTO
# pyrefly: ignore [missing-import]
from app.schemas.webhook import TradingViewWebhookSchema
# pyrefly: ignore [missing-import]
from app.trading.trading_service import TradingService
# pyrefly: ignore [missing-import]
from app.trading.state_manager import state_manager

class MockAsyncSession:
    """Mock asynchronous SQLAlchemy session for fast unit testing."""
    def __init__(self):
        self.added = []
        self.committed = False
        self.flushed = False

    def add(self, entity):
        self.added.append(entity)
        if not hasattr(entity, "id") or entity.id is None:
            entity.id = len(self.added)

    async def flush(self):
        self.flushed = True

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass

@pytest.fixture
def mock_db():
    return MockAsyncSession()

@pytest.fixture
def trading_service(mock_broker):
    return TradingService(mock_broker)

@pytest.mark.asyncio
async def test_buy_signal_pipeline_success(trading_service, mock_db):
    """Verifies BUY signal execution from end to end."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        timeframe="M15",
        price=2650.00,
        sl=2645.00,
        tp=2660.00,
        risk_percent=1.0
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(True, "LONDON")):
        success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=1, db=mock_db)

    assert success is True
    assert message == "FILLED"
    # Verify signal entity status
    signals = [e for e in mock_db.added if isinstance(e, Signal)]
    assert len(signals) == 1
    assert signals[0].status == SignalStatus.EXECUTED

@pytest.mark.asyncio
async def test_sell_signal_pipeline_success(trading_service, mock_db):
    """Verifies SELL signal execution from end to end."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.SELL,
        timeframe="M15",
        price=2650.00,
        sl=2655.00,
        tp=2640.00,
        risk_percent=1.0
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(True, "NEW_YORK")):
        success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=2, db=mock_db)

    assert success is True
    assert message == "FILLED"

@pytest.mark.asyncio
async def test_invalid_signal_missing_mandatory_sl(trading_service, mock_db):
    """Verifies rejection of invalid signal missing mandatory Stop Loss."""
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=None, # Missing SL
        tp=2660.00
    )

    success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=3, db=mock_db)
    assert success is False
    assert "Stop loss" in message

@pytest.mark.asyncio
async def test_duplicate_signal_protection(trading_service):
    """Verifies idempotency and duplicate signal protection."""
    payload = {
        "symbol": "XAUUSD",
        "action": "BUY",
        "timeframe": "M15",
        "bar_time": "2026-10-09T12:00:00",
        "price": "2650.00"
    }
    h = trading_service.deduplication.compute_hash(payload)

    is_dup1, _ = trading_service.deduplication.is_duplicate(h)
    assert is_dup1 is False

    is_dup2, _ = trading_service.deduplication.is_duplicate(h)
    assert is_dup2 is True

@pytest.mark.asyncio
async def test_session_rejection(trading_service, mock_db):
    """Verifies rejection when outside of allowed trading sessions."""
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(False, "OUTSIDE_ALLOWED_SESSIONS")):
        success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=4, db=mock_db)

    assert success is False
    assert "session inactive" in message

@pytest.mark.asyncio
async def test_spread_rejection(trading_service, mock_db):
    """Verifies rejection when market spread exceeds limit."""
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(True, "LONDON")):
        with patch.object(trading_service.session_service, "validate_spread", return_value=(False, 45.0, "Spread (45.0) exceeds maximum")):
            success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=5, db=mock_db)

    assert success is False
    assert "Spread" in message

@pytest.mark.asyncio
async def test_risk_rejection_when_bot_paused(trading_service, mock_db):
    """Verifies risk rejection when bot is in PAUSED state."""
    state_manager.pause_trading(reason="Maintenance", operator="TEST")
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(True, "LONDON")):
        success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=6, db=mock_db)

    assert success is False
    assert "PAUSED" in message

@pytest.mark.asyncio
async def test_max_position_limit_rejection(trading_service, mock_db):
    """Verifies rejection when open position limit is reached."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(True, "LONDON")):
        with patch.object(trading_service.position_service, "get_active_positions", return_value=[object(), object()]): # 2 positions
            success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=7, db=mock_db)

    assert success is False
    assert "Position limit reached" in message

@pytest.mark.asyncio
async def test_broker_execution_failure(trading_service, mock_db):
    """Verifies handling when broker returns execution rejection."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00
    )

    failed_result = OrderExecutionResultDTO(
        success=False,
        retcode=10015, # Invalid price
        error_message="Invalid price rejected by MT5"
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(True, "LONDON")):
        with patch.object(trading_service.broker_service, "execute_market_order", return_value=failed_result):
            success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=8, db=mock_db)

    assert success is False
    assert "Invalid price" in message

@pytest.mark.asyncio
async def test_fail_safe_uncertain_execution_no_auto_retry(trading_service, mock_db):
    """
    CRITICAL FAIL-SAFE: Verifies that uncertain network/broker results are marked
    as UNCERTAIN and NEVER automatically resubmitted.
    """
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00
    )

    uncertain_result = OrderExecutionResultDTO(
        success=False,
        retcode=10004, # Requote / Timeout uncertain
        error_message="Broker trade timeout"
    )

    with patch.object(trading_service.session_service, "is_session_active", return_value=(True, "LONDON")):
        with patch.object(trading_service.broker_service, "execute_market_order", return_value=uncertain_result):
            success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=9, db=mock_db)

    assert success is False
    assert "UNCERTAIN" in message
    assert "DO NOT resubmit" in message

@pytest.mark.asyncio
async def test_mt5_disconnection_rejection(trading_service, mock_db):
    """Verifies that trading is immediately halted if broker MT5 connection is down."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00
    )

    with patch.object(trading_service.broker_service, "ensure_connected", return_value=False):
        success, message = await trading_service.handle_webhook_signal(payload, webhook_event_id=10, db=mock_db)

    assert success is False
    assert "disconnected" in message
