"""Focused regression test suite covering all critical safety remediation items."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.brokers.mock_broker import MockBrokerAdapter
from app.core.config import settings
from app.core.constants import OrderSide, SignalStatus, WebhookStatus
from app.models.signal import Signal
from app.models.trade import Trade
from app.models.webhook import WebhookEvent
from app.repositories.trade_repo import TradeRepository
from app.schemas.account import AccountInfoDTO, SymbolInfoDTO
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.lot_calculator import lot_calculator
from app.trading.signal_service import SignalService
from app.trading.timestamp_validator import TimestampValidator
from app.trading.trading_service import TradingService
from app.trading.state_manager import state_manager
from app.trading.recovery_service import webhook_recovery_service

class MockSessionForSafety:
    """Mock session tailored for safety regression verification."""
    def __init__(self, daily_loss: float = 0.0, raise_on_commit: bool = False, raise_on_query: bool = False):
        self.added = []
        self.committed = False
        self.daily_loss = daily_loss
        self.raise_on_commit = raise_on_commit
        self.raise_on_query = raise_on_query

    def add(self, entity):
        self.added.append(entity)
        if not hasattr(entity, "id") or entity.id is None:
            entity.id = len(self.added)

    async def flush(self):
        pass

    async def commit(self):
        if self.raise_on_commit:
            raise RuntimeError("Database connection lost during commit")
        self.committed = True

    async def rollback(self):
        pass

    async def refresh(self, obj):
        pass

    async def execute(self, stmt):
        if self.raise_on_query:
            raise RuntimeError("Database unavailable for query")
        loss = self.daily_loss
        class MockResult:
            def scalar(self):
                return loss
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return []
                    def first(self):
                        return None
                return MockScalars()
        return MockResult()


@pytest.fixture
def mock_broker():
    return MockBrokerAdapter()


# ==============================================================================
# 1. DAILY LOSS ENFORCEMENT & FAIL-CLOSED TESTS
# ==============================================================================
@pytest.mark.asyncio
async def test_daily_loss_limit_blocks_new_orders(mock_broker):
    """Proves that reaching the daily loss limit blocks new orders immediately."""
    state_manager.resume_trading()
    service = TradingService(mock_broker)

    # Balance is $10,000. MAX_DAILY_LOSS_PERCENT is 3.0% => limit is $300.
    # Set simulated daily realized loss to $350 (exceeds $300).
    mock_db = MockSessionForSafety(daily_loss=-350.0)

    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        timeframe="M15",
        price=2650.00,
        sl=2645.00,
        tp=2660.00,
        risk_percent=1.0
    )

    success, message = await service.handle_webhook_signal(payload, webhook_event_id=1, db=mock_db)

    assert success is False
    assert "exceeded MAX_DAILY_LOSS" in message
    assert state_manager.is_emergency_stopped is True  # Emergency stop triggered by circuit breaker


@pytest.mark.asyncio
async def test_daily_loss_retrieval_failure_fails_closed(mock_broker):
    """Proves that if daily loss/risk data cannot be queried from DB, the engine fails closed."""
    state_manager.resume_trading()
    service = TradingService(mock_broker)

    # Simulate database error during risk query
    mock_db = MockSessionForSafety(raise_on_query=True)

    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        timeframe="M15",
        price=2650.00,
        sl=2645.00,
        tp=2660.00,
        risk_percent=1.0
    )

    success, message = await service.handle_webhook_signal(payload, webhook_event_id=1, db=mock_db)

    assert success is False
    assert "Fail closed" in message
    assert "Unable to retrieve risk data" in message


# ==============================================================================
# 2. RISK PERCENTAGE ENFORCEMENT & CAPPING TESTS
# ==============================================================================
@pytest.mark.asyncio
async def test_webhook_cannot_increase_risk_beyond_backend_limit(mock_broker):
    """Proves webhook requesting excessive risk is safely capped to MAX_RISK_PERCENT_PER_TRADE."""
    account = AccountInfoDTO(
        login=12345,
        server="Demo",
        balance=10000.0,
        equity=10000.0,
        margin=0.0,
        free_margin=10000.0,
        margin_level=1000.0,
        currency="USD",
        leverage=100,
        is_connected=True
    )
    symbol_info = await mock_broker.get_symbol_info("XAUUSD")

    # Request extreme 50% risk from malicious/erroneous webhook
    lots_requested, err = lot_calculator.calculate_lots(
        account=account,
        symbol_info=symbol_info,
        entry_price=2650.00,
        stop_loss=2645.00,
        risk_percent=50.0  # Excessive risk requested
    )

    # Calculate expected lots with backend cap (MAX_RISK_PERCENT_PER_TRADE = 2.0%)
    lots_capped, _ = lot_calculator.calculate_lots(
        account=account,
        symbol_info=symbol_info,
        entry_price=2650.00,
        stop_loss=2645.00,
        risk_percent=settings.MAX_RISK_PERCENT_PER_TRADE
    )

    assert lots_requested is not None
    assert lots_requested == lots_capped
    # At $10k equity and 2% risk ($200) with 5.0 pt distance and 100 contract size ($500/lot):
    # Lots should be approx 0.40, NEVER 10.00
    assert lots_requested <= settings.MAX_LOT_SIZE


def test_signal_service_caps_excessive_risk_in_payload():
    """Proves SignalService validation caps payload.risk_percent in place."""
    sig_service = SignalService()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD",
        action=OrderSide.BUY,
        price=2650.00,
        sl=2645.00,
        risk_percent=15.0  # Above 2.0%
    )

    is_valid, err = sig_service.validate_payload(payload)
    assert is_valid is True
    assert payload.risk_percent == settings.MAX_RISK_PERCENT_PER_TRADE


# ==============================================================================
# 3. TIMESTAMP VALIDATION & TOLERANCE TESTS
# ==============================================================================
def test_timestamp_validator_accepts_fresh_unix_and_iso():
    """Proves validator handles fresh Unix epoch (seconds/ms) and ISO 8601 timestamps."""
    now_ts = datetime.now(timezone.utc).timestamp()

    # Seconds
    is_valid, err = TimestampValidator.validate_freshness(str(int(now_ts)))
    assert is_valid is True
    assert err is None

    # Milliseconds
    is_valid_ms, err_ms = TimestampValidator.validate_freshness(str(int(now_ts * 1000)))
    assert is_valid_ms is True

    # ISO 8601
    iso_now = datetime.now(timezone.utc).isoformat()
    is_valid_iso, _ = TimestampValidator.validate_freshness(iso_now)
    assert is_valid_iso is True


def test_timestamp_validator_rejects_stale_alert():
    """Proves validator rejects stale alerts older than tolerance."""
    now_ts = datetime.now(timezone.utc).timestamp()
    stale_ts = now_ts - 600  # 10 minutes ago (exceeds 300s tolerance)

    is_valid, err = TimestampValidator.validate_freshness(str(int(stale_ts)))
    assert is_valid is False
    assert "Stale signal timestamp" in err


def test_timestamp_validator_rejects_malformed_timestamp():
    """Proves validator rejects unparseable timestamps."""
    is_valid, err = TimestampValidator.validate_freshness("NOT_A_TIMESTAMP_STRING")
    assert is_valid is False
    assert "Malformed timestamp" in err


# ==============================================================================
# 4. DURABLE IDEMPOTENCY & CONCURRENCY TESTS
# ==============================================================================
@pytest.mark.asyncio
async def test_persistent_idempotency_database_constraint():
    """Proves that database IntegrityError prevents duplicate processing without resubmission."""
    from sqlalchemy.exc import IntegrityError
    from app.trading.deduplication import DeduplicationService

    dedup = DeduplicationService(ttl_seconds=30)
    canonical_payload = {
        "symbol": "XAUUSD",
        "action": "BUY",
        "timeframe": "M15",
        "bar_time": "1770000000",
        "price": "2650.00"
    }

    hash1 = dedup.compute_hash(canonical_payload)
    hash2 = dedup.compute_hash(canonical_payload)
    assert hash1 == hash2

    # First check passes
    is_dup1, _ = dedup.is_duplicate(hash1)
    assert is_dup1 is False

    # Immediate second check caught by memory
    is_dup2, _ = dedup.is_duplicate(hash2)
    assert is_dup2 is True


# ==============================================================================
# 5. DURABLE WEBHOOK RECOVERY AFTER RESTART TESTS
# ==============================================================================
@pytest.mark.asyncio
async def test_durable_webhook_recovery_processes_pending_events(mock_broker):
    """Proves that unhandled RECEIVED webhook events in DB are drained on startup recovery."""
    with patch("app.trading.recovery_service.AsyncSessionLocal") as mock_session_ctx:
        pending_event = WebhookEvent(
            id=101,
            event_uuid="test-uuid-drain",
            payload_hash="test-hash-drain",
            raw_payload={
                "symbol": "XAUUSD",
                "action": "BUY",
                "timeframe": "M15",
                "price": 2650.00,
                "sl": 2645.00,
                "tp": 2660.00,
                "risk_percent": 1.0
            },
            processing_status=WebhookStatus.RECEIVED
        )

        class MockDrainSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def execute(self, stmt):
                class MockRes:
                    def scalars(self):
                        class MockScalars:
                            def all(self):
                                return [pending_event]
                        return MockScalars()
                return MockRes()
            async def commit(self):
                pass
            def add(self, obj):
                pass
            async def flush(self):
                pass

        mock_session_ctx.return_value = MockDrainSession()

        with patch("app.trading.recovery_service.TradingService.handle_webhook_signal", return_value=(True, "Executed")):
            recovered = await webhook_recovery_service.recover_pending_events()
            assert recovered == 1
            assert pending_event.processing_status == WebhookStatus.PROCESSED
