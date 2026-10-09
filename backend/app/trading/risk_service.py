"""Risk evaluation and lot sizing service with independent final authority."""
import time
from typing import Optional
from loguru import logger
# pyrefly: ignore [missing-import]
from app.brokers.base import IBrokerAdapter
# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.core.constants import OrderSide, RiskAction, RiskEventType
# pyrefly: ignore [missing-import]
from app.schemas.account import AccountInfoDTO, SymbolInfoDTO
# pyrefly: ignore [missing-import]
from app.schemas.risk import RiskValidationResultDTO
# pyrefly: ignore [missing-import]
from app.schemas.webhook import TradingViewWebhookSchema
# pyrefly: ignore [missing-import]
from app.trading.lot_calculator import lot_calculator
# pyrefly: ignore [missing-import]
from app.trading.state_manager import state_manager

class RiskService:
    """
    Independent Risk Management Engine with final authority over whether a new trade may be executed.
    Guarantees:
    - risk_per_trade enforcement
    - max_daily_loss circuit breaker
    - max_open_positions limit
    - max_lot_size & min_lot_size constraints
    - max_consecutive_losses circuit breaker
    - cooldown_after_loss timer enforcement
    - minimum margin level protection
    - If required information is unavailable: REJECTS THE TRADE (no guessing).
    """

    def __init__(self, broker: IBrokerAdapter):
        self.broker = broker
        self._consecutive_losses = 0
        self._last_loss_timestamp: Optional[float] = None

    @property
    def consecutive_losses(self) -> int:
        return self._consecutive_losses

    def record_loss(self):
        """Records a realized loss, updates consecutive loss count and triggers cooldown."""
        self._consecutive_losses += 1
        self._last_loss_timestamp = time.time()
        logger.warning(
            f"Loss recorded. Consecutive losses: {self._consecutive_losses}/{settings.MAX_CONSECUTIVE_LOSSES}. "
            f"Cooldown active for {settings.COOLDOWN_MINUTES_AFTER_LOSS}m."
        )

        if self._consecutive_losses >= settings.MAX_CONSECUTIVE_LOSSES:
            reason = f"Hit {self._consecutive_losses} consecutive losses. Pausing trading automatically."
            logger.error(reason)
            state_manager.pause_trading(reason=reason, operator="RISK_ENGINE")

    def record_win(self):
        """Resets consecutive loss counter upon profitable trade."""
        self._consecutive_losses = 0
        logger.info("Profitable trade recorded. Consecutive losses counter reset to 0.")

    def is_in_cooldown(self) -> bool:
        """Checks if trading cooldown period after a loss is currently active."""
        if self._last_loss_timestamp is None:
            return False
        elapsed_seconds = time.time() - self._last_loss_timestamp
        cooldown_seconds = settings.COOLDOWN_MINUTES_AFTER_LOSS * 60
        return elapsed_seconds < cooldown_seconds

    def get_remaining_cooldown_seconds(self) -> float:
        if self._last_loss_timestamp is None:
            return 0.0
        elapsed_seconds = time.time() - self._last_loss_timestamp
        cooldown_seconds = settings.COOLDOWN_MINUTES_AFTER_LOSS * 60
        return max(0.0, cooldown_seconds - elapsed_seconds)

    async def validate_signal(
        self,
        payload: TradingViewWebhookSchema,
        account: Optional[AccountInfoDTO],
        symbol_info: Optional[SymbolInfoDTO],
        open_positions_count: int,
        daily_loss_realized: float = 0.0
    ) -> RiskValidationResultDTO:
        # 0. Safety Rule: If required broker/account/symbol information is unavailable -> REJECT
        if account is None:
            return RiskValidationResultDTO(
                is_valid=False,
                reason="Account information is unavailable from broker. Cannot execute safely.",
                rule_name="SAFETY_DATA_UNAVAILABLE",
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        if symbol_info is None:
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Symbol specification for '{payload.symbol}' is unavailable from broker. Do not guess.",
                rule_name="SAFETY_DATA_UNAVAILABLE",
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        # 1. Consecutive Losses Circuit Breaker (Prioritized to identify pause reason)
        if self._consecutive_losses >= settings.MAX_CONSECUTIVE_LOSSES:
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Max consecutive losses ({self._consecutive_losses}) reached limit ({settings.MAX_CONSECUTIVE_LOSSES}).",
                rule_name=RiskEventType.CONSECUTIVE_LOSS_PAUSE.value,
                action_taken=RiskAction.BOT_PAUSED
            )

        # 2. Bot State Check (RUNNING vs PAUSED / EMERGENCY_STOP)
        if not state_manager.is_running:
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Bot in {state_manager.current_state.value} mode. New trades prohibited.",
                rule_name=RiskEventType.BOT_STATE_RESTRICTION.value,
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        # 3. Cooldown Timer Check
        if self.is_in_cooldown():
            rem = self.get_remaining_cooldown_seconds()
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Trading is in cooldown period after recent loss ({rem:.0f}s remaining).",
                rule_name="COOLDOWN_AFTER_LOSS",
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        # 4. Maximum Open Positions Limit
        if open_positions_count >= settings.MAX_OPEN_POSITIONS and payload.action in [OrderSide.BUY, OrderSide.SELL]:
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Open positions ({open_positions_count}) reached MAX_OPEN_POSITIONS ({settings.MAX_OPEN_POSITIONS}).",
                rule_name="MAX_OPEN_POSITIONS",
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        # 4. Daily Loss Circuit Breaker
        max_daily_loss = account.balance * (settings.MAX_DAILY_LOSS_PERCENT / 100.0)
        if daily_loss_realized >= max_daily_loss:
            reason = f"Daily realized loss ${daily_loss_realized:.2f} exceeded MAX_DAILY_LOSS ${max_daily_loss:.2f} ({settings.MAX_DAILY_LOSS_PERCENT}%)."
            # pyrefly: ignore [missing-import]
            from app.notifications.telegram_bot import telegram_bot
            telegram_bot.notify_daily_loss_reached(daily_loss=daily_loss_realized, cap=max_daily_loss)
            state_manager.trigger_emergency_stop(reason, operator="RISK_ENGINE")
            return RiskValidationResultDTO(
                is_valid=False,
                reason=reason,
                rule_name=RiskEventType.DAILY_LOSS_BREACH.value,
                action_taken=RiskAction.EMERGENCY_STOP_TRIGGERED
            )


        # 5. Mandatory Stop Loss Check
        if payload.action in [OrderSide.BUY, OrderSide.SELL]:
            if payload.sl is None or payload.sl <= 0:
                return RiskValidationResultDTO(
                    is_valid=False,
                    reason="Stop Loss is strictly mandatory. Unprotected trades are forbidden.",
                    rule_name="MANDATORY_STOP_LOSS",
                    action_taken=RiskAction.SIGNAL_REJECTED
                )

        # 6. Minimum Margin Level Check (Prevent margin calls)
        if account.margin_level is not None and account.margin_level < 200.0:
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Account margin level ({account.margin_level:.1f}%) is below minimum safe threshold (200.0%).",
                rule_name=RiskEventType.MARGIN_CALL_PROTECT.value,
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        # 7. Deterministic Lot Size Calculation
        entry_price = payload.price if payload.price else (symbol_info.ask if payload.action == OrderSide.BUY else symbol_info.bid)
        lots, err_msg = lot_calculator.calculate_lots(
            account=account,
            symbol_info=symbol_info,
            entry_price=entry_price,
            stop_loss=payload.sl,
            risk_percent=payload.risk_percent
        )

        if lots is None:
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Lot calculation rejected: {err_msg}",
                rule_name=RiskEventType.INVALID_LOT_SIZE.value,
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        # 8. Bounds check on calculated lot
        if lots < symbol_info.lot_min or lots > settings.MAX_LOT_SIZE:
            return RiskValidationResultDTO(
                is_valid=False,
                reason=f"Calculated lot size {lots} is outside allowable limits [{symbol_info.lot_min}, {settings.MAX_LOT_SIZE}].",
                rule_name=RiskEventType.INVALID_LOT_SIZE.value,
                action_taken=RiskAction.SIGNAL_REJECTED
            )

        return RiskValidationResultDTO(
            is_valid=True,
            calculated_lots=lots,
            reason="All risk controls passed successfully."
        )
