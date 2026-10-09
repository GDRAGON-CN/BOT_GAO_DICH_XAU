"""Extensive unit test suite for dedicated Risk Management Engine and Lot Calculator."""
import pytest
# pyrefly: ignore [missing-import]
from app.brokers.mock_broker import MockBrokerAdapter
# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.core.constants import OrderSide, RiskAction, RiskEventType
# pyrefly: ignore [missing-import]
from app.schemas.account import AccountInfoDTO, SymbolInfoDTO
# pyrefly: ignore [missing-import]
from app.schemas.webhook import TradingViewWebhookSchema
# pyrefly: ignore [missing-import]
from app.trading.lot_calculator import LotCalculator
# pyrefly: ignore [missing-import]
from app.trading.risk_service import RiskService
# pyrefly: ignore [missing-import]
from app.trading.state_manager import state_manager

@pytest.fixture
def risk_service(mock_broker):
    return RiskService(mock_broker)

@pytest.fixture
def standard_account():
    return AccountInfoDTO(
        login=123456,
        balance=10000.0,
        equity=10000.0,
        margin=200.0,
        free_margin=9800.0,
        margin_level=5000.0,
        currency="USD"
    )

@pytest.fixture
def gold_symbol_specs():
    return SymbolInfoDTO(
        name="XAUUSD",
        point=0.01,
        digits=2,
        spread_points=18.0,
        bid=2650.00,
        ask=2650.20,
        lot_min=0.01,
        lot_max=50.0,
        lot_step=0.01,
        trade_contract_size=100.0, # 100 oz per standard lot
        tick_size=0.01,
        tick_value=1.00 # $1 per 0.01 move per 1.0 lot
    )

# ==============================================================================
# 1. LOT CALCULATOR UNIT TESTS
# ==============================================================================

def test_lot_calculator_normal_risk(standard_account, gold_symbol_specs):
    """
    Equity: $10,000, 1% risk = $100.
    Entry: $2650.00, SL: $2645.00 -> $5.00 distance.
    Loss per 1.0 lot = 5.00 * 100 = $500.
    Expected lot: 100 / 500 = 0.20 lots.
    """
    lots, err = LotCalculator.calculate_lots(
        account=standard_account,
        symbol_info=gold_symbol_specs,
        entry_price=2650.00,
        stop_loss=2645.00,
        risk_percent=1.0
    )
    assert err is None
    assert lots == 0.20

def test_lot_calculator_very_small_account(gold_symbol_specs):
    """
    Very small account: Equity $20, 1% risk = $0.20.
    Entry: $2650.00, SL: $2640.00 -> $10 distance.
    Loss for minimum lot 0.01 = $10 * 100 * 0.01 = $10.00, which is 50x target risk.
    Safety mechanism must REJECT this trade to protect account from blowing up.
    """
    small_account = AccountInfoDTO(
        login=999, balance=20.0, equity=20.0, margin=0.0, free_margin=20.0, margin_level=1000.0
    )
    lots, err = LotCalculator.calculate_lots(
        account=small_account,
        symbol_info=gold_symbol_specs,
        entry_price=2650.00,
        stop_loss=2640.00,
        risk_percent=1.0
    )
    assert lots is None
    assert "Account too small" in err

def test_lot_calculator_large_stop_loss(standard_account, gold_symbol_specs):
    """
    Huge stop loss distance: $2650.00 down to $2550.00 ($100 distance).
    1% risk = $100.
    1.0 lot loss = $10,000.
    Raw lot: 100 / 10000 = 0.01 lots.
    """
    lots, err = LotCalculator.calculate_lots(
        account=standard_account,
        symbol_info=gold_symbol_specs,
        entry_price=2650.00,
        stop_loss=2550.00,
        risk_percent=1.0
    )
    assert err is None
    assert lots == 0.01

def test_lot_calculator_small_stop_loss_clamped_to_max(standard_account, gold_symbol_specs):
    """
    Tiny stop loss: Entry $2650.00, SL $2649.90 ($0.10 distance).
    1% risk = $100.
    Loss per 1.0 lot = 0.10 * 100 = $10.
    Raw lot: 100 / 10 = 10.0 lots.
    System MAX_LOT_SIZE is 1.00 -> Must clamp to 1.00 lot safely.
    """
    lots, err = LotCalculator.calculate_lots(
        account=standard_account,
        symbol_info=gold_symbol_specs,
        entry_price=2650.00,
        stop_loss=2649.90,
        risk_percent=1.0
    )
    assert err is None
    assert lots == settings.MAX_LOT_SIZE

def test_lot_calculator_invalid_symbol_info(standard_account):
    """Safety check: Missing symbol info must be REJECTED, not guessed."""
    lots, err = LotCalculator.calculate_lots(
        account=standard_account,
        symbol_info=None,
        entry_price=2650.00,
        stop_loss=2645.00
    )
    assert lots is None
    assert "Symbol specifications are unavailable" in err

# ==============================================================================
# 2. RISK SERVICE COMPREHENSIVE VALIDATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_risk_validation_normal_pass(risk_service, standard_account, gold_symbol_specs):
    """Valid trade passes all checks."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(
        symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00, tp=2660.00, risk_percent=1.0
    )
    res = await risk_service.validate_signal(
        payload=payload, account=standard_account, symbol_info=gold_symbol_specs, open_positions_count=0
    )
    assert res.is_valid is True
    assert res.calculated_lots == 0.20

@pytest.mark.asyncio
async def test_risk_rejection_trading_paused(risk_service, standard_account, gold_symbol_specs):
    """Reject when bot state is PAUSED."""
    state_manager.pause_trading(reason="Manual intervention", operator="TEST")
    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00)
    res = await risk_service.validate_signal(
        payload=payload, account=standard_account, symbol_info=gold_symbol_specs, open_positions_count=0
    )
    assert res.is_valid is False
    assert res.rule_name == RiskEventType.BOT_STATE_RESTRICTION.value

@pytest.mark.asyncio
async def test_risk_rejection_emergency_stop(risk_service, standard_account, gold_symbol_specs):
    """Reject when bot state is EMERGENCY_STOP."""
    state_manager.trigger_emergency_stop(reason="Crash protection", operator="TEST")
    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00)
    res = await risk_service.validate_signal(
        payload=payload, account=standard_account, symbol_info=gold_symbol_specs, open_positions_count=0
    )
    assert res.is_valid is False
    assert "EMERGENCY_STOP" in res.reason

@pytest.mark.asyncio
async def test_risk_daily_loss_circuit_breaker(risk_service, standard_account, gold_symbol_specs):
    """When daily loss breaches 3%, trigger Emergency Stop and reject signal."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00)
    # 3% of $10,000 = $300. We pass $350 realized daily loss.
    res = await risk_service.validate_signal(
        payload=payload,
        account=standard_account,
        symbol_info=gold_symbol_specs,
        open_positions_count=0,
        daily_loss_realized=350.0
    )
    assert res.is_valid is False
    assert res.rule_name == RiskEventType.DAILY_LOSS_BREACH.value
    assert res.action_taken == RiskAction.EMERGENCY_STOP_TRIGGERED
    assert not state_manager.is_running

@pytest.mark.asyncio
async def test_risk_consecutive_losses_circuit_breaker(risk_service, standard_account, gold_symbol_specs):
    """Hit 3 consecutive losses -> pause bot and reject further trades."""
    state_manager.resume_trading()
    risk_service.record_loss()
    risk_service.record_loss()
    risk_service.record_loss() # Hit 3rd loss

    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00)
    res = await risk_service.validate_signal(
        payload=payload, account=standard_account, symbol_info=gold_symbol_specs, open_positions_count=0
    )
    assert res.is_valid is False
    assert res.rule_name == RiskEventType.CONSECUTIVE_LOSS_PAUSE.value

@pytest.mark.asyncio
async def test_risk_cooldown_timer_rejection(risk_service, standard_account, gold_symbol_specs):
    """Trade rejected during cooldown timer following a loss."""
    state_manager.resume_trading()
    # Reset count to 1 (under consecutive loss pause limit) but trigger cooldown
    risk_service._consecutive_losses = 1
    risk_service._last_loss_timestamp = pytest.importorskip("time").time() # just now

    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00)
    res = await risk_service.validate_signal(
        payload=payload, account=standard_account, symbol_info=gold_symbol_specs, open_positions_count=0
    )
    assert res.is_valid is False
    assert res.rule_name == "COOLDOWN_AFTER_LOSS"

@pytest.mark.asyncio
async def test_risk_insufficient_margin_level(risk_service, gold_symbol_specs):
    """Reject signal if account margin level is below safe minimum (< 200%)."""
    state_manager.resume_trading()
    low_margin_acc = AccountInfoDTO(
        login=123, balance=1000.0, equity=1000.0, margin=800.0, free_margin=200.0, margin_level=125.0
    )
    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00)
    res = await risk_service.validate_signal(
        payload=payload, account=low_margin_acc, symbol_info=gold_symbol_specs, open_positions_count=0
    )
    assert res.is_valid is False
    assert res.rule_name == RiskEventType.MARGIN_CALL_PROTECT.value

@pytest.mark.asyncio
async def test_risk_missing_broker_info_safety(risk_service, standard_account):
    """Safety guarantee: Reject if broker symbol info is None."""
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.00, sl=2645.00)
    res = await risk_service.validate_signal(
        payload=payload, account=standard_account, symbol_info=None, open_positions_count=0
    )
    assert res.is_valid is False
    assert res.rule_name == "SAFETY_DATA_UNAVAILABLE"
