import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.notifications.telegram_bot import TelegramNotificationService
from app.monitoring.health import HealthChecker
from app.monitoring.telemetry import telemetry

@pytest.mark.asyncio
async def test_telegram_does_not_fail_on_network_error():
    service = TelegramNotificationService()
    service.enabled = True
    service.bot_token = "mock_token"
    service.chat_id = "mock_chat"

    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
        # Must return False and NOT raise an uncaught exception
        res = await service.send_message("Test message")
        assert res is False

@pytest.mark.asyncio
async def test_telegram_does_not_fail_trade_pipeline():
    """Verify that when Telegram fails or throws, trade pipeline continues unaffected."""
    service = TelegramNotificationService()
    service.enabled = True

    # Calling any notification helper must never raise
    with patch.object(service, "notify_async", side_effect=Exception("Telegram socket crash")):
        try:
            service.notify_new_signal(symbol="XAUUSD", action="BUY", timeframe="M15")
        except Exception:
            pytest.fail("Telegram notification raised an exception in caller thread")

@pytest.mark.asyncio
async def test_health_check_endpoint():
    mock_broker = MagicMock()
    mock_broker.is_connected = AsyncMock(return_value=True)

    checker = HealthChecker(mock_broker)
    telemetry.record_webhook()
    telemetry.record_execution()
    telemetry.record_account_sync()

    with patch("app.monitoring.health.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session


        health = await checker.check()
        assert health["status"] == "healthy"
        assert health["components"]["backend"]["status"] == "healthy"
        assert health["components"]["mysql"]["status"] == "healthy"
        assert health["components"]["mt5"]["connected"] is True
        assert health["telemetry"]["last_webhook_received_at"] is not None
        assert health["telemetry"]["last_successful_execution_at"] is not None
        assert health["telemetry"]["last_account_sync_at"] is not None
