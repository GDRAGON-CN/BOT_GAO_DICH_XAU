from app.core.constants import BotState
from app.trading.state_manager import BotStateManager

def test_state_transitions():
    sm = BotStateManager()
    assert sm.current_state == BotState.PAUSED

    sm.resume_trading("TEST_OP")
    assert sm.is_running

    sm.trigger_emergency_stop("TEST_REASON", "TEST_OP")
    assert sm.is_emergency_stopped
    assert sm.emergency_reason == "TEST_REASON"
