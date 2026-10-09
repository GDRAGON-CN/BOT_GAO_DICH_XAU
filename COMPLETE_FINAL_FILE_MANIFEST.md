# Complete Final File Manifest

**Repository Root**: `d:\BOT Giao dịch`  
**Generated Date**: 2026-10-09  
**System**: XAUUSD Automated Gold Trading System  

---

## 1. File Classification & Inventory

| File Path | Purpose | Status | Dependencies | Local Required? | VPS Required? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `.env.example` | Complete environment variables template with descriptions | Active | None | Yes | Yes |
| `.env` | Active local environment configuration | Local Only | None | Yes | No (Configured on VPS) |
| `.gitignore` | Git exclusions for sensitive configs, cache, and builds | Active | Git | Yes | Yes |
| `pyproject.toml` | Pytest and tool configurations | Active | Python, Pytest | Yes | Yes |
| `requirements.txt` | Production Python dependencies | Active | pip | Yes | Yes |
| `requirements-dev.txt`| Developer and test dependencies | Active | pip | Yes | No |
| `README.md` | Primary developer documentation & 33-point guide | Active | Markdown | Yes | Yes |
| `backend\alembic.ini` | Database migration configuration | Active | Alembic, MySQL | Yes | Yes |
| `backend\app\main.py` | FastAPI application factory, lifespan, and startup reconciliation | Active | FastAPI, Uvicorn | Yes | Yes |
| `backend\app\core\config.py` | Pydantic Settings loader with .env and YAML loading | Active | pydantic-settings | Yes | Yes |
| `backend\app\core\constants.py` | System enums (OrderSide, SignalStatus, BotState, etc.) | Active | Enum | Yes | Yes |
| `backend\app\core\logging.py` | Loguru logging configuration with 20MB file rotation | Active | Loguru | Yes | Yes |
| `backend\app\core\security.py` | Webhook and Dashboard API token verification | Active | hmac, hashlib | Yes | Yes |
| `backend\app\database\base.py` | SQLAlchemy DeclarativeBase definition | Active | SQLAlchemy | Yes | Yes |
| `backend\app\database\session.py`| Async and sync SQLAlchemy session factories | Active | aiomysql, pymysql | Yes | Yes |
| `backend\app\models\account.py` | `AccountSnapshot` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\audit.py` | `BotEvent` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\order.py` | `Order` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\position.py`| `Position` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\risk.py` | `RiskEvent` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\signal.py` | `Signal` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\strategy_config.py` | `StrategyConfig` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\trade.py` | `Trade` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\trading_session.py` | `TradingSession` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\models\webhook.py` | `WebhookEvent` entity model | Active | SQLAlchemy | Yes | Yes |
| `backend\app\monitoring\health.py` | Liveness and readiness health evaluation | Active | SQLAlchemy, MT5 | Yes | Yes |
| `backend\app\monitoring\metrics.py` | Metrics Aggregator for dashboard telemetry | Active | Repositories, Broker | Yes | Yes |
| `backend\app\monitoring\telemetry.py` | System telemetry tracker (last execution/sync) | Active | Python | Yes | Yes |
| `backend\app\monitoring\watchdog.py` | Terminal connection supervisor & protect daemon | Active | asyncio, broker | Yes | Yes |
| `backend\app\notifications\base.py` | `INotificationService` abstract interface | Active | abc | Yes | Yes |
| `backend\app\notifications\telegram_bot.py` | Non-blocking Telegram notification service | Active | httpx, loguru | Yes | Yes |
| `backend\app\repositories\account_repo.py` | Database access for account snapshots | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\audit_repo.py` | Database access for bot audit events | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\base.py` | Base CRUD repository | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\config_repo.py`| Database access for strategy configurations | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\order_repo.py` | Database access for orders | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\position_repo.py`| Database access for positions | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\signal_repo.py`| Database access for signals | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\trade_repo.py` | Database access for closed trades | Active | SQLAlchemy | Yes | Yes |
| `backend\app\repositories\webhook_repo.py`| Database access for webhook events | Active | SQLAlchemy | Yes | Yes |
| `backend\app\schemas\account.py`| Pydantic DTOs for account and symbol specs | Active | Pydantic | Yes | Yes |
| `backend\app\schemas\control.py`| Pydantic schemas for state control commands | Active | Pydantic | Yes | Yes |
| `backend\app\schemas\order.py` | Pydantic schemas for order requests & results | Active | Pydantic | Yes | Yes |
| `backend\app\schemas\position.py`| Pydantic schemas for position tracking | Active | Pydantic | Yes | Yes |
| `backend\app\schemas\risk.py` | Pydantic schemas for risk validation results | Active | Pydantic | Yes | Yes |
| `backend\app\schemas\signal.py` | Pydantic schemas for canonical signals | Active | Pydantic | Yes | Yes |
| `backend\app\schemas\webhook.py`| Pydantic schemas for incoming TradingView payloads | Active | Pydantic | Yes | Yes |
| `backend\app\trading\broker_service.py` | Broker orchestration and connectivity layer | Active | IBrokerAdapter | Yes | Yes |
| `backend\app\trading\deduplication.py` | SHA-256 in-memory & DB idempotency protection | Active | hashlib, time | Yes | Yes |
| `backend\app\trading\execution_engine.py` | Execution orchestrator with risk gating | Active | Broker, Risk | Yes | Yes |
| `backend\app\trading\execution_service.py` | Granular execution and fail-safe handler | Active | Broker, DB | Yes | Yes |
| `backend\app\trading\lot_calculator.py` | Deterministic lot calculator using contract specs | Active | Decimal | Yes | Yes |
| `backend\app\trading\position_manager.py` | Broker position modification & closing | Active | Broker | Yes | Yes |
| `backend\app\trading\position_service.py` | Position queries, limits, and closures | Active | Broker | Yes | Yes |
| `backend\app\trading\reconciliation_service.py` | MT5 Broker vs MySQL post-startup reconciler | Active | Broker, DB | Yes | Yes |
| `backend\app\trading\risk_engine.py` | Risk engine validating lot size & account checks | Active | Broker | Yes | Yes |
| `backend\app\trading\risk_service.py` | Independent Risk Service with circuit breakers | Active | StateManager | Yes | Yes |
| `backend\app\trading\session_service.py` | Session hours and spread validation service | Active | datetime | Yes | Yes |
| `backend\app\trading\session_validator.py` | Session validator helper | Active | datetime | Yes | Yes |
| `backend\app\trading\signal_service.py` | Canonical signal construction and validation | Active | Pydantic, DB | Yes | Yes |
| `backend\app\trading\state_manager.py` | State machine (RUNNING, PAUSED, EMERGENCY_STOP) | Active | Python | Yes | Yes |
| `backend\app\trading\trading_service.py` | Complete pipeline orchestrator | Active | All services | Yes | Yes |
| `backend\app\api\v1\endpoints\control.py` | Control REST API (resume, pause, emergency-stop) | Active | FastAPI | Yes | Yes |
| `backend\app\api\v1\endpoints\dashboard.py` | Dashboard REST API (metrics, history tables) | Active | FastAPI | Yes | Yes |
| `backend\app\api\v1\endpoints\health.py` | System health evaluation REST API | Active | FastAPI | Yes | Yes |
| `backend\app\api\v1\endpoints\webhook.py` | TradingView webhook ingestion REST API | Active | FastAPI | Yes | Yes |
| `backend\brokers\base.py` | `IBrokerAdapter` abstract interface | Active | abc | Yes | Yes |
| `backend\brokers\mock_broker.py` | In-memory paper broker adapter for tests | Active | IBrokerAdapter | Yes | Yes |
| `backend\brokers\mt5_adapter.py` | Native MetaTrader5 broker adapter | Active | MetaTrader5 | Yes | Yes |
| `backend\scripts\check_mt5_link.py` | Command-line MT5 link diagnostic probe | Active | MetaTrader5 | Yes | Yes |
| `backend\scripts\init_mysql.sql` | MySQL Workbench schema initialization script | Active | MySQL 8+ | Yes | Yes |
| `backend\scripts\seed_db.py` | Initial database seeding script | Active | SQLAlchemy | Yes | Yes |
| `backend\scripts\test_webhook.py` | Simulated webhook testing script | Active | httpx | Yes | Yes |
| `backend\tests\conftest.py` | Pytest fixtures (mock_broker, sample_account) | Active | pytest | Yes | No |
| `backend\tests\unit\test_config_validation.py` | Settings & risk thresholds tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_database_layer.py` | Entity insert, update, rollback, constraints tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_deduplication.py` | Idempotency and duplicate detection tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_e2e_simulation.py` | Full pipeline zero-risk simulation test | Active | pytest | Yes | No |
| `backend\tests\unit\test_lot_calculator.py` | Lot calculation unit tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_reconciliation.py` | Offline position closure reconciliation tests | Active | pytest | No | No |
| `backend\tests\unit\test_risk_engine.py` | Risk bounds unit tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_risk_management_engine.py`| Comprehensive circuit breaker tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_session_validator.py` | Trading session time validation tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_state_manager.py` | State machine transition tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_telegram_and_health.py` | Telegram fault isolation & health tests | Active | pytest | Yes | No |
| `backend\tests\unit\test_trading_engine.py` | Full trading engine pipeline unit tests | Active | pytest | Yes | No |
| `frontend\index.html` | Dashboard HTML entrypoint | Active | HTML5 | Yes | Yes |
| `frontend\package.json` | Frontend dependencies and build scripts | Active | npm | Yes | Yes |
| `frontend\vite.config.js` | Vite bundler configuration | Active | Vite | Yes | Yes |
| `frontend\src\main.jsx` | React root mount point | Active | React | Yes | Yes |
| `frontend\src\App.jsx` | Main dashboard view container | Active | React | Yes | Yes |
| `frontend\src\index.css` | Premium dark-mode styling rules | Active | CSS | Yes | Yes |
| `frontend\src\components\Header.jsx` | Header with DEMO MODE badge | Active | React | Yes | Yes |
| `frontend\src\components\HistoryViewer.jsx` | Historical auditing tabbed views | Active | React | Yes | Yes |
| `frontend\src\components\MetricsGrid.jsx` | Account metrics and PnL display cards | Active | React | Yes | Yes |
| `frontend\src\components\OrdersHistory.jsx` | Executed orders table component | Active | React | Yes | Yes |
| `frontend\src\components\PositionsTable.jsx` | Live open positions table component | Active | React | Yes | Yes |
| `frontend\src\components\SignalsFeed.jsx` | Real-time signal feed component | Active | React | Yes | Yes |
| `frontend\src\components\StateControls.jsx` | Control buttons with confirmation dialogs | Active | React | Yes | Yes |
| `frontend\src\services\api.js` | REST client connecting to backend | Active | fetch | Yes | Yes |
| `pine\gold_strategy.pine` | TradingView Pine Script v5 strategy | Active | Pine Script | Yes | Yes |
| `pine\README.md` | Guide for TradingView alert setup | Active | Markdown | Yes | Yes |
| `scripts\start-backend.bat` | Starts FastAPI server on port 8000 | Active | Windows Batch | Yes | Yes |
| `scripts\stop-backend.bat` | Stops background backend process | Active | Windows Batch | Yes | Yes |
| `scripts\start-frontend.bat` | Starts Vite dev server on port 5173 | Active | Windows Batch | Yes | Yes |
| `scripts\health-check.bat` | Probes system health endpoint | Active | Windows Batch | Yes | Yes |
| `scripts\database-migration.bat` | Executes Alembic schema upgrades | Active | Windows Batch | Yes | Yes |
| `scripts\database-backup.bat` | Exports timestamped mysqldump | Active | Windows Batch | Yes | Yes |
| `scripts\test-pipeline.bat` | Sends test webhook signal | Active | Windows Batch | Yes | Yes |
| `deployment\vps\caddy_config.Caddyfile` | Production TLS reverse proxy config | Active | Caddy | No | Yes |
| `deployment\vps\install_nssm_services.bat` | 24/7 Windows service supervisor installer | Active | NSSM | No | Yes |
| `docs\DATABASE.md` | Database schema & queries guide | Active | Markdown | Yes | Yes |
| `docs\LOCAL_DEVELOPMENT.md` | Windows local run guide | Active | Markdown | Yes | Yes |
| `docs\VPS_DEPLOYMENT.md` | Windows VPS migration guide | Active | Markdown | Yes | Yes |
| `docs\TRADINGVIEW_WEBHOOK.md` | Webhook alert payload guide | Active | Markdown | Yes | Yes |
| `docs\MT5_VANTAGE.md` | MT5 and Vantage integration details | Active | Markdown | Yes | Yes |
| `docs\ARCHITECTURE.md` | Architecture design document | Active | Markdown | Yes | Yes |
