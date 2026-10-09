"""
End-to-End Simulation Test:
TradingView-like Webhook
↓
Signal Validation
↓
Risk Engine
↓
Mock MT5 Broker Execution
↓
Database Record
↓
Telegram Mock
↓
Dashboard State Update

Zero real money risk (100% paper/mock execution).
"""
import pytest
import time
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timezone

from app.brokers.mock_broker import MockBrokerAdapter
from app.core.constants import OrderSide, OrderStatus, SignalStatus, BotState
from app.schemas.webhook import TradingViewWebhookSchema
from app.trading.state_manager import state_manager
from app.trading.trading_service import TradingService
from app.notifications.telegram_bot import telegram_bot
from app.monitoring.metrics import MetricsAggregator
from app.repositories.signal_repo import SignalRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.position_repo import PositionRepository

class MockDatabaseSession:
    """Mock asynchronous DB session recording entities and state changes."""
    def __init__(self):
        self.entities = []
        self.committed = False

    def add(self, obj):
        self.entities.append(obj)
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = len(self.entities)

    async def flush(self):
        pass

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass

    async def execute(self, stmt):
        class MockResult:
            def scalar(self):
                return 0.0
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return []
                    def first(self):
                        return None
                return MockScalars()
        return MockResult()

@pytest.mark.asyncio
async def test_complete_end_to_end_flow_zero_risk():
    """
    Executes full lifecycle simulation without broker dependencies or financial risk:
    1. System is in RUNNING state.
    2. Simulated webhook arrives from TradingView.
    3. Signal is verified and stored.
    4. Risk engine evaluates balance, spread, lot sizing, and circuit breakers.
    5. Mock MT5 adapter executes market order and returns filled ticket.
    6. Position and Order are committed to database.
    7. Telegram notification is dispatched safely.
    8. Dashboard telemetry and metrics reflect the new position.
    """
    # 1. Initialize Bot in RUNNING state
    state_manager.resume_trading(operator="E2E_SIMULATOR")
    assert state_manager.current_state == BotState.RUNNING

    # 2. Setup isolated Mock Broker and Database
    mock_broker = MockBrokerAdapter()
    await mock_broker.initialize()
    mock_db = MockDatabaseSession()
    trading_service = TradingService(mock_broker)

    # 3. Formulate TradingView Alert Payload
    alert_payload = TradingViewWebhookSchema(
        event_id=f"e2e_evt_{int(time.time())}",
        symbol="XAUUSD",
        action=OrderSide.BUY,
        timeframe="M15",
        price=2650.00,
        sl=2645.00,
        tp=2665.00,
        risk_percent=1.0,
        strategy_name="gold_m15_breakout",
        secret="tv_local_test_secret_123456"
    )

    # 4. Mock Telegram safely to record outbound alerts
    telegram_messages = []
    with patch.object(telegram_bot, "send_message", new=AsyncMock(side_effect=lambda msg: telegram_messages.append(msg))):
        with patch("app.notifications.telegram_bot.TelegramNotificationService._safe_dispatch") as mock_dispatch:
            mock_dispatch.side_effect = lambda text: telegram_messages.append(text)

            # 5. Execute Signal through Trading Engine
            success, message = await trading_service.handle_webhook_signal(
                payload=alert_payload,
                webhook_event_id=101,
                db=mock_db
            )

            # Assert execution success
            assert success is True
            assert message == "FILLED"
            assert mock_db.committed is True

            # 6. Verify Database Persistence (Signal, Order, Position)
            types_in_db = [type(e).__name__ for e in mock_db.entities]
            assert "Signal" in types_in_db
            assert "Order" in types_in_db
            assert "Position" in types_in_db

            signal_entity = next(e for e in mock_db.entities if type(e).__name__ == "Signal")
            assert signal_entity.status == SignalStatus.EXECUTED
            assert signal_entity.symbol == "XAUUSD"

            order_entity = next(e for e in mock_db.entities if type(e).__name__ == "Order")
            assert order_entity.execution_status == OrderStatus.FILLED
            assert float(order_entity.filled_lots) > 0.0

            position_entity = next(e for e in mock_db.entities if type(e).__name__ == "Position")
            assert position_entity.broker_position_ticket > 0

            # 7. Verify Telegram Mock Notifications
            assert len(telegram_messages) >= 2  # New signal, order submitted/filled
            assert any("NEW SIGNAL" in m for m in telegram_messages)
            assert any("ORDER FILLED" in m or "POSITION OPENED" in m for m in telegram_messages)

            # 8. Verify Dashboard State / Metrics Aggregator
            open_positions = await mock_broker.get_open_positions()
            assert len(open_positions) == 1
            assert open_positions[0].symbol == "XAUUSD"
            assert open_positions[0].lots == float(order_entity.filled_lots)
