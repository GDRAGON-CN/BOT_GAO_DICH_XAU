import pytest
from app.core.constants import OrderSide, RiskEventType
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.state_manager import state_manager

@pytest.mark.asyncio
async def test_risk_blocks_when_bot_paused(risk_engine, sample_account, sample_gold_symbol):
    state_manager.pause_trading()
    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.0, sl=2645.0)
    res = await risk_engine.validate_signal(payload, sample_account, sample_gold_symbol, 0)
    assert not res.is_valid
    assert res.rule_name == RiskEventType.BOT_STATE_RESTRICTION.value

@pytest.mark.asyncio
async def test_risk_mandatory_stop_loss(risk_engine, sample_account, sample_gold_symbol):
    state_manager.resume_trading()
    payload = TradingViewWebhookSchema(symbol="XAUUSD", action=OrderSide.BUY, price=2650.0, sl=None)
    res = await risk_engine.validate_signal(payload, sample_account, sample_gold_symbol, 0)
    assert not res.is_valid
    assert res.rule_name == "MANDATORY_STOP_LOSS"
