import asyncio
from loguru import logger
from app.brokers.base import IBrokerAdapter
from app.notifications.telegram_bot import telegram_bot
from app.trading.state_manager import state_manager

class TerminalWatchdog:
    """Supervises broker connectivity and takes protective actions if connection drops."""

    def __init__(self, broker: IBrokerAdapter, poll_interval_sec: int = 30):
        self.broker = broker
        self.poll_interval_sec = poll_interval_sec
        self._running = False

    async def start(self):
        self._running = True
        logger.info("Terminal watchdog daemon started.")
        while self._running:
            try:
                connected = await self.broker.is_connected()
                if not connected and state_manager.is_running:
                    logger.warning("Watchdog detected broker disconnect while RUNNING. Pausing bot.")
                    telegram_bot.notify_mt5_disconnected(reason="Broker terminal disconnected during watchdog polling")
                    state_manager.pause_trading(
                        reason="Broker terminal disconnected",
                        operator="WATCHDOG"
                    )

            except Exception as e:
                logger.error(f"Watchdog error: {e}")

            await asyncio.sleep(self.poll_interval_sec)

    def stop(self):
        self._running = False
        logger.info("Terminal watchdog daemon stopped.")
