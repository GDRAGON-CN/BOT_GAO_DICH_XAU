import asyncio
import httpx
from loguru import logger
from app.core.config import settings
from app.notifications.base import INotificationService

class TelegramNotificationService(INotificationService):
    """
    Dedicated Telegram notification service for trade alerts and bot health events.
    Design Principle:
    - Notification system only.
    - Zero authority to bypass the Risk Engine or modify trading decisions.
    - If Telegram fails, it MUST NEVER fail the trade or system operation.
    - Errors are caught and logged.
    """

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = bool(settings.TELEGRAM_ENABLE_ALERTS and self.bot_token and self.chat_id)

    async def send_message(self, text: str) -> bool:
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    logger.error(f"Telegram notification returned status {res.status_code}: {res.text}")
                    return False
                return True
        except Exception as e:
            # Under NO circumstance does Telegram failure fail any trading action
            logger.error(f"Telegram send failed (trading unaffected): {e}")
            return False

    def notify_async(self, text: str) -> None:
        """Dispatches notification asynchronously without blocking caller."""
        if self.enabled:
            try:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.send_message(text))
                except RuntimeError:
                    try:
                        asyncio.run(self.send_message(text))
                    except Exception as exc:
                        logger.error(f"Failed to run telegram async notification: {exc}")
            except Exception as e:
                logger.error(f"Telegram notify_async error: {e}")

    def _safe_dispatch(self, text: str):
        try:
            self.notify_async(text)
        except Exception as e:
            logger.error(f"Telegram safe dispatch error: {e}")


    # ==========================================
    # DOMAIN-SPECIFIC NOTIFICATION HELPERS
    # ==========================================

    def notify_new_signal(self, symbol: str, action: str, timeframe: str, entry: float = None, sl: float = None, tp: float = None):
        msg = (
            f"📡 *NEW SIGNAL RECEIVED*\n"
            f"• *Symbol*: `{symbol}`\n"
            f"• *Action*: *{action}*\n"
            f"• *Timeframe*: `{timeframe}`\n"
            f"• *Entry Target*: `{entry if entry else 'Market'}`\n"
            f"• *SL / TP*: `{sl}` / `{tp}`"
        )
        self._safe_dispatch(msg)

    def notify_signal_rejected(self, symbol: str, action: str, reason: str):
        msg = (
            f"❌ *SIGNAL REJECTED*\n"
            f"• *Symbol*: `{symbol}` | *Action*: *{action}*\n"
            f"• *Reason*: {reason}"
        )
        self._safe_dispatch(msg)

    def notify_order_submitted(self, symbol: str, action: str, lots: float, price: float = None):
        msg = (
            f"📝 *ORDER SUBMITTED*\n"
            f"• *Order*: {action} {lots:.2f} lots `{symbol}`\n"
            f"• *Requested Price*: `{price if price else 'Market'}`"
        )
        self._safe_dispatch(msg)

    def notify_order_filled(self, ticket: int, symbol: str, action: str, lots: float, fill_price: float):
        msg = (
            f"🚀 *ORDER FILLED*\n"
            f"• *Ticket*: `#{ticket}`\n"
            f"• *Order*: *{action}* {lots:.2f} lots `{symbol}`\n"
            f"• *Execution Price*: `{fill_price:.2f}`"
        )
        self._safe_dispatch(msg)

    def notify_position_opened(self, ticket: int, symbol: str, side: str, lots: float, entry: float, sl: float = None, tp: float = None):
        msg = (
            f"📈 *POSITION OPENED*\n"
            f"• *Ticket*: `#{ticket}`\n"
            f"• *Position*: *{side}* {lots:.2f} `{symbol}` @ `{entry:.2f}`\n"
            f"• *SL*: `{sl}` | *TP*: `{tp}`"
        )
        self._safe_dispatch(msg)

    def notify_position_closed(self, ticket: int, symbol: str, close_price: float, profit: float, reason: str = "MANUAL"):
        outcome_emoji = "🟢" if profit >= 0 else "🔴"
        outcome_text = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
        msg = (
            f"{outcome_emoji} *POSITION CLOSED*\n"
            f"• *Ticket*: `#{ticket}` (`{symbol}`)\n"
            f"• *Close Price*: `{close_price:.2f}`\n"
            f"• *P/L*: *{outcome_text}*\n"
            f"• *Reason*: `{reason}`"
        )
        self._safe_dispatch(msg)

    def notify_profit(self, trade_id: int, symbol: str, profit: float, pips: float = 0.0):
        msg = (
            f"🎉 *PROFIT TARGET HIT*\n"
            f"• *Trade*: `#{trade_id}` (`{symbol}`)\n"
            f"• *Net Profit*: `+${profit:.2f}`\n"
            f"• *Gain*: `+{pips:.1f} pips`"
        )
        self._safe_dispatch(msg)

    def notify_loss(self, trade_id: int, symbol: str, loss: float, pips: float = 0.0):
        msg = (
            f"⚠️ *STOP LOSS HIT*\n"
            f"• *Trade*: `#{trade_id}` (`{symbol}`)\n"
            f"• *Loss*: `-${abs(loss):.2f}`\n"
            f"• *Pips*: `-{abs(pips):.1f} pips`"
        )
        self._safe_dispatch(msg)

    def notify_risk_rejection(self, rule_name: str, details: str):
        msg = (
            f"🛡️ *RISK ENGINE REJECTION*\n"
            f"• *Rule*: `{rule_name}`\n"
            f"• *Details*: {details}"
        )
        self._safe_dispatch(msg)

    def notify_daily_loss_reached(self, daily_loss: float, cap: float):
        msg = (
            f"🛑 *DAILY LOSS LIMIT REACHED*\n"
            f"• *Today's Loss*: `-${daily_loss:.2f}`\n"
            f"• *Max Drawdown Cap*: `-${cap:.2f}`\n"
            f"• *Action*: Trading paused / Emergency stop triggered."
        )
        self._safe_dispatch(msg)

    def notify_mt5_disconnected(self, reason: str = "Heartbeat failed"):
        msg = (
            f"🔌 *MT5 TERMINAL DISCONNECTED*\n"
            f"• *Alert*: Lost connection to MT5 terminal!\n"
            f"• *Details*: {reason}\n"
            f"• *Protective Action*: Trading paused automatically."
        )
        self._safe_dispatch(msg)

    def notify_database_error(self, error: str):
        msg = (
            f"💾 *DATABASE ERROR DETECTED*\n"
            f"• *Details*: `{error}`\n"
            f"• *Notice*: Running in protective mode."
        )
        self._safe_dispatch(msg)

    def notify_emergency_stop(self, reason: str, operator: str = "SYSTEM"):
        msg = (
            f"🚨 *EMERGENCY STOP TRIGGERED*\n"
            f"• *Reason*: {reason}\n"
            f"• *Triggered By*: `{operator}`\n"
            f"• *Status*: All trade signal entries blocked."
        )
        self._safe_dispatch(msg)

    def notify_app_startup(self, env: str, version: str = "1.0.0"):
        msg = (
            f"🚀 *APPLICATION STARTUP*\n"
            f"• *Service*: XAUUSD Trading Engine v{version}\n"
            f"• *Environment*: `{env}`\n"
            f"• *Status*: Initialized and monitoring."
        )
        self._safe_dispatch(msg)

    def notify_app_shutdown(self, env: str):
        msg = (
            f"🛑 *APPLICATION SHUTDOWN*\n"
            f"• *Service*: XAUUSD Trading Engine\n"
            f"• *Environment*: `{env}`\n"
            f"• *Status*: Clean shutdown sequence completed."
        )
        self._safe_dispatch(msg)

telegram_bot = TelegramNotificationService()

