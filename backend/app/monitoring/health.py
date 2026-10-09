"""Comprehensive Health Monitoring for Trading System."""
from datetime import datetime, timezone
from typing import Any, Dict
from loguru import logger
from sqlalchemy import text
from app.brokers.base import IBrokerAdapter
from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.monitoring.telemetry import telemetry
from app.notifications.telegram_bot import telegram_bot
from app.trading.state_manager import state_manager

class HealthChecker:
    """
    Evaluates:
    - Backend health (running process)
    - MySQL health (can execute SELECT 1)
    - MT5 health & Broker connectivity (broker.is_connected())
    - Last TradingView webhook received timestamp
    - Last successful order execution timestamp
    - Last account telemetry sync timestamp
    """

    def __init__(self, broker: IBrokerAdapter):
        self.broker = broker

    async def check(self) -> Dict[str, Any]:
        # 1. MT5 & Broker Connectivity
        broker_ok = False
        try:
            broker_ok = await self.broker.is_connected()
        except Exception as e:
            logger.error(f"Health check broker connection error: {e}")
            telegram_bot.notify_mt5_disconnected(str(e))

        # 2. MySQL Database Check
        db_ok = False
        db_latency_ms = 0.0
        try:
            t0 = datetime.now(timezone.utc)
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            db_latency_ms = round((datetime.now(timezone.utc) - t0).total_seconds() * 1000, 2)
            db_ok = True
        except Exception as exc:
            logger.error(f"Health check database error: {exc}")
            telegram_bot.notify_database_error(str(exc))

        # Overall Status Assessment
        overall_status = "healthy"
        if not db_ok or not broker_ok:
            overall_status = "unhealthy" if (not db_ok and not broker_ok) else "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.APP_ENV,
            "bot_state": state_manager.current_state.value,
            "components": {
                "backend": {
                    "status": "healthy",
                    "uptime_mode": "online"
                },
                "mysql": {
                    "status": "healthy" if db_ok else "unreachable",
                    "latency_ms": db_latency_ms if db_ok else None
                },
                "mt5": {
                    "status": "connected" if broker_ok else "disconnected",
                    "broker": "Vantage MT5",
                    "server": settings.MT5_SERVER,
                    "connected": broker_ok
                }

            },
            "telemetry": {
                "last_webhook_received_at": telemetry.last_webhook_received_at.isoformat() if telemetry.last_webhook_received_at else None,
                "last_successful_execution_at": telemetry.last_successful_execution_at.isoformat() if telemetry.last_successful_execution_at else None,
                "last_account_sync_at": telemetry.last_account_sync_at.isoformat() if telemetry.last_account_sync_at else None
            }
        }
