from typing import Optional
from loguru import logger
from app.core.constants import BotState
from app.notifications.telegram_bot import telegram_bot

class BotStateManager:
    """Manages system state machine: RUNNING, PAUSED, EMERGENCY_STOP."""

    def __init__(self):
        self._state = BotState.PAUSED
        self._emergency_reason: Optional[str] = None

    @property
    def current_state(self) -> BotState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state == BotState.RUNNING

    @property
    def is_paused(self) -> bool:
        return self._state == BotState.PAUSED

    @property
    def is_emergency_stopped(self) -> bool:
        return self._state == BotState.EMERGENCY_STOP

    @property
    def emergency_reason(self) -> Optional[str]:
        return self._emergency_reason

    def resume_trading(self, operator: str = "SYSTEM") -> BotState:
        prev = self._state
        self._state = BotState.RUNNING
        self._emergency_reason = None
        logger.info(f"Bot state: {prev} -> RUNNING (by {operator})")
        telegram_bot.notify_async(f"🟢 *BOT RESUMED*: State is now RUNNING ({operator})")
        return self._state

    def pause_trading(self, reason: str = "Operator paused", operator: str = "SYSTEM") -> BotState:
        prev = self._state
        self._state = BotState.PAUSED
        logger.info(f"Bot state: {prev} -> PAUSED (by {operator}: {reason})")
        telegram_bot.notify_async(f"🟡 *BOT PAUSED*: New entries suspended ({reason})")
        return self._state

    def trigger_emergency_stop(self, reason: str, operator: str = "SYSTEM") -> BotState:
        prev = self._state
        self._state = BotState.EMERGENCY_STOP
        self._emergency_reason = reason
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason} (by {operator})")
        telegram_bot.notify_emergency_stop(reason=reason, operator=operator)
        return self._state


state_manager = BotStateManager()
