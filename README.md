# XAUUSD Automated Gold Trading System

A production-grade, personal automated trading system linking **TradingView**, **FastAPI**, **MetaTrader 5 (Vantage)**, and **MySQL 8+**, designed with strict safety boundaries, deterministic risk calculation, and 24/7 resilience on Windows and Windows VPS.

---

## 1. Project Overview & Design Philosophy

This trading engine automates execution of the **XAUUSD (Gold)** strategy from TradingView alerts to MetaTrader 5 via Vantage.
* **Separation of Concerns**: TradingView only generates signals; it has **no direct authority** to execute trades.
* **Deterministic Risk Engine**: Every order must pass through session checks, spread checks, lot size calculations, position count limits, and consecutive loss cooldowns.
* **Demo-First Safety**: The application defaults to **DEMO MODE**. It will never silently execute against a live account.
* **Zero Rewrites for VPS**: Runs locally on Windows without Docker, and migrates seamlessly to a Windows Server VPS using the exact same codebase.

---

## 2. Main Features

* **TradingView Webhook Integration**: Authenticated, deduplicated alert listener with timestamp validation.
* **Pine Script v5 Strategy**: Multi-indicator Gold strategy (`pine/gold_strategy.pine`) tailored for M15 XAUUSD.
* **MetaTrader 5 Broker Adapter**: Native Python `MetaTrader5` integration for Vantage Demo and Live accounts with MockBroker for automated testing.
* **Dynamic Lot Sizing**: Computes position sizes based on equity, entry price, stop-loss distance, and broker contract specifications (`trade_contract_size`, tick size, tick value).
* **Circuit Breakers**: Daily loss cap (3.0%), maximum open positions limit (2), maximum spread limit (35 points), consecutive losses cooldown (3 losses = 30m pause).
* **React 18 Dashboard**: Clear operational UI showing account balance, equity, free margin, margin level, today's P/L, daily loss, open positions, and state controls.
* **State Control & Confirmation**: `START TRADING`, `PAUSE TRADING`, and `EMERGENCY STOP` with confirmation modals to prevent accidental clicks.
* **Auditing & History**: Historical tabbed views for Signals, Orders, Positions, Closed Trades, Risk Events, and Bot Events.
* **Outbound Telegram Alerts**: Real-time notifications for orders, fills, rejections, closed positions, profit/loss, daily limits, and MT5 status without blocking trading execution.
* **24/7 Resilience & Startup Reconciliation**: Self-healing post-startup reconciliation synchronizes broker state with MySQL after any unexpected crash or restart.

---

## 3. System Architecture

```
                  ┌───────────────────────────────┐
                  │      TradingView Alert        │
                  │  (XAUUSD Pine Script v5)      │
                  └──────────────┬────────────────┘
                                 │ HTTPS (Port 443 via Caddy)
                                 ▼
                  ┌───────────────────────────────┐
                  │    POST /api/webhooks/...     │
                  │   (FastAPI Background Task)   │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │       Signal Validation       │
                  │    (Schema, Action, Mandatory │
                  │       Stop Loss, Dedup)       │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │     Trading Session Gate      │
                  │    (London, New York, Spread) │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │       Risk Engine Gate        │
                  │ (Daily Loss, Cooldown, Limits,│
                  │   Deterministic Lot Sizing)   │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │       Execution Engine        │
                  │    (Fail-safe retcode check)  │
                  └──────────────┬────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
  ┌──────────────────────────────┐ ┌──────────────────────────────┐
  │ MetaTrader 5 Terminal (Win32)│ │  MySQL 8+ Database (Private) │
  │ Vantage Demo / Live Engine   │ │  Signals, Orders, Positions, │
  └──────────────┬───────────────┘ │  Trades, Audit Events        │
                 │                 └──────────────────────────────┘
                 ▼                               │
  ┌──────────────────────────────┐               ▼
  │ Outbound Telegram Alerts     │ ┌──────────────────────────────┐
  │ (Non-blocking notifications) │ │ React 18 / Vite Dashboard    │
  └──────────────────────────────┘ └──────────────────────────────┘
```

---

## 4. Technology Stack

* **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Loguru, HTTPX.
* **Database & ORM**: MySQL 8.0+, SQLAlchemy 2.0 (asyncio + sync), Alembic.
* **Broker SDK**: `MetaTrader5` (Win32 API) for Vantage International.
* **Frontend**: React 18, Vite, Lucide Icons, Vanilla CSS (dark theme).
* **Testing**: Pytest, Pytest-Asyncio.
* **Deployment & Networking**: Caddy (Auto HTTPS), NSSM (Windows Service Manager), Windows Batch scripts.

---

## 5. Folder Structure

```
d:\BOT Giao dịch\
├── .env.example                     # Environment template
├── .env                             # Local active configuration (Never committed)
├── requirements.txt                 # Production Python dependencies
├── requirements-dev.txt             # Development & testing dependencies
├── pyproject.toml                   # Pytest tool configurations
├── README.md                        # Primary developer documentation
├── backend/
│   ├── alembic.ini                  # Alembic migration settings
│   ├── alembic/                     # Database migration versions
│   ├── app/
│   │   ├── main.py                  # FastAPI factory & lifespan
│   │   ├── api/v1/                  # REST endpoints (health, control, dashboard, webhook)
│   │   ├── brokers/                 # Broker abstraction (base, mt5_adapter, mock_broker)
│   │   ├── core/                    # Settings, constants, logging, security
│   │   ├── database/                # SQLAlchemy session, engine, declarative Base
│   │   ├── models/                  # DB entities (signals, orders, positions, trades, events)
│   │   ├── monitoring/              # Health checker, metrics aggregator, watchdog daemon
│   │   ├── notifications/           # Telegram bot service & domain alert helpers
│   │   ├── repositories/            # SQL query repository classes
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   └── trading/                 # Trading services: Signal, Risk, Session, Position, Execution
│   ├── scripts/                     # Utility scripts (test_webhook.py, init_mysql.sql)
│   └── tests/unit/                  # Comprehensive unit & E2E simulation test suite
├── frontend/                        # React 18 + Vite personal dashboard
│   ├── src/
│   │   ├── App.jsx                  # Main dashboard component
│   │   ├── components/              # MetricsGrid, PositionsTable, StateControls, HistoryViewer
│   │   └── services/api.js          # REST client communicating with FastAPI
│   └── package.json                 # Node dependencies
├── pine/
│   └── gold_strategy.pine           # TradingView Pine Script v5 strategy for XAUUSD
├── deployment/
│   ├── vps/                         # Caddyfile, NSSM installer, and watchdog XML
│   └── local/                       # Local configuration notes
├── docs/                            # Deep-dive guides:
│   ├── DATABASE.md                  # Schema definitions & SQL Workbench queries
│   ├── LOCAL_DEVELOPMENT.md         # Windows local setup guide without Docker
│   ├── VPS_DEPLOYMENT.md            # Windows VPS 24/7 migration guide
│   └── TRADINGVIEW_WEBHOOK.md       # Alert payload and webhook specifications
└── scripts/                         # Windows native .bat automation scripts
    ├── start-backend.bat            # Starts FastAPI server
    ├── stop-backend.bat             # Stops background backend process
    ├── start-frontend.bat           # Starts Vite dev server
    ├── health-check.bat             # Probes system health endpoint
    ├── database-migration.bat       # Executes Alembic schema upgrades
    ├── database-backup.bat          # Takes timestamped mysqldump backup
    └── test-pipeline.bat            # Sends end-to-end test webhook signal
```

---

## 6. Database Architecture

MySQL 8+ is the application's single source of persistent truth.
* **`webhook_events`**: Raw incoming TradingView webhook payloads, hashes, source IP, idempotency tracking.
* **`signals`**: Canonical trade signals (`symbol`, `action`, `entry`, `sl`, `tp`, `status`, `rejection_reason`).
* **`orders`**: Orders submitted to broker (`broker_order_ticket`, `requested_lots`, `filled_lots`, `execution_price`, `status`).
* **`positions`**: Open and closed positions with live broker tickets, side, entry price, and stop levels.
* **`trades`**: Historical closed trades with net profit, commissions, swap, pips, and exit reasons (`SL_HIT`, `TP_HIT`, `MANUAL`).
* **`account_snapshots`**: Time-series snapshots of balance, equity, margin, and floating P/L.
* **`risk_events`**: Violations caught by the Risk Engine (`rule_name`, `threshold_value`, `actual_value`, `system_action`).
* **`bot_events`**: Audit log of bot state transitions (`RUNNING`, `PAUSED`, `EMERGENCY_STOP`), operators, and reconciliation events.
* **`trading_sessions`**: Active session definitions (`LONDON`, `NEW_YORK`, `ASIAN`) and max allowed spreads.

---

## 7. MySQL Workbench Setup

1. Open **MySQL Workbench**.
2. Connect to local instance (`127.0.0.1:3306`).
3. Open [`backend/scripts/init_mysql.sql`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/backend/scripts/init_mysql.sql) and execute (⚡) to create `tradebot_db` and standard tables.
4. Run migrations via Alembic:
   ```cmd
   python -m alembic upgrade head
   ```
5. Use MySQL Workbench **only** for viewing tables, inspecting data, and database administration. Never put business logic inside triggers or stored procedures.

---

## 8. TradingView Setup

1. Open **TradingView** on a chart for **XAUUSD** (Gold).
2. Set timeframe to **15m (M15)**.
3. Open the **Pine Editor** at the bottom of the TradingView interface.
4. Paste the strategy from [`pine/gold_strategy.pine`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/pine/gold_strategy.pine).
5. Click **Add to Chart**.

---

## 9. Pine Script Setup

The script [`pine/gold_strategy.pine`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/pine/gold_strategy.pine) is parameterized and allows configuration of:
* Trend EMA Period (default: 200 EMA)
* Fast & Slow EMAs (default: 9 / 21 EMA)
* ATR Length & Multiplier for Stop Loss and Take Profit
* RSI Filter (default: 14)
* Risk Percentage (default: 1.0%)

---

## 10. Webhook Alert Configuration

1. In TradingView, click **Create Alert** on the XAUUSD chart.
2. Under **Condition**, select `Gold M15 Automation Strategy`.
3. Select **Order fills only** or **Alert() function calls**.
4. Check **Webhook URL** and enter your endpoint:
   * Local (via tunnel): `https://your-tunnel.ngrok-free.app/api/webhooks/tradingview`
   * VPS (via Caddy): `https://tradebot.yourdomain.com/api/webhooks/tradingview`
5. In the alert **Message** body, enter:
```json
{
  "event_id": "{{strategy.order.id}}",
  "symbol": "XAUUSD",
  "action": "{{strategy.order.action}}",
  "timeframe": "M15",
  "price": {{strategy.order.price}},
  "sl": {{plot("StopLoss")}},
  "tp": {{plot("TakeProfit")}},
  "risk_percent": 1.0,
  "strategy_name": "gold_m15_v1",
  "timestamp": "{{time}}",
  "secret": "YOUR_WEBHOOK_SECRET_HERE"
}
```

---

## 11. MetaTrader 5 (MT5) Setup

1. Install MetaTrader 5 on Windows.
2. In the top toolbar, ensure the **Algo Trading** button is enabled (Green icon).
3. Open `Tools -> Options -> Expert Advisors`:
   * Check: **Allow algorithmic trading**
   * Check: **Allow DLL imports**
4. Keep the terminal running on your desktop.

---

## 12. Vantage Broker Setup

1. Open a demo account with **Vantage Markets** (Server: `VantageInternational-Demo`).
2. In MT5, click `File -> Login to Trade Account`.
3. Enter your demo account number, password, and select server `VantageInternational-Demo`.
4. Ensure the Market Watch shows `XAUUSD` with active real-time bid/ask prices.

---

## 13. Local Installation (Windows)

Prerequisites: Python 3.10+, Node.js 18+, MySQL Server 8.0+.

```cmd
git clone https://github.com/your-repo/bot-trading.git "d:\BOT Giao dịch"
cd "d:\BOT Giao dịch"

python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt

cd frontend
npm install
cd ..
```

---

## 14. Environment Variables (`.env`)

Copy `.env.example` to `.env` and configure:
```ini
APP_ENV=local
DEBUG=true
TRADING_ENV=DEMO

SERVER_HOST=127.0.0.1
SERVER_PORT=8000
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=tradebot_user
DB_PASSWORD=YOUR_PASSWORD
DB_NAME=tradebot_db

MT5_PATH=
MT5_LOGIN=YOUR_DEMO_LOGIN
MT5_PASSWORD=YOUR_DEMO_PASSWORD
MT5_SERVER=VantageInternational-Demo
MT5_TIMEOUT_MS=10000

DEFAULT_SYMBOL=XAUUSD
BROKER_SYMBOL_MAP={"XAUUSD":"XAUUSD"}

WEBHOOK_SECRET=tv_local_test_secret_123456
DASHBOARD_API_KEY=dash_local_secret_123456

RISK_PERCENT_PER_TRADE=1.0
MAX_DAILY_LOSS_PERCENT=3.0
MAX_OPEN_POSITIONS=2
MAX_LOT_SIZE=1.00
MIN_LOT_SIZE=0.01
MAX_SPREAD_POINTS=35.0
MAX_SLIPPAGE_POINTS=20.0
MAX_CONSECUTIVE_LOSSES=3
COOLDOWN_MINUTES_AFTER_LOSS=30
ALLOW_TRADING_SESSIONS=["LONDON","NEW_YORK","ASIAN"]

TELEGRAM_ENABLE_ALERTS=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

## 15. Database Migration

Run Alembic migrations to build and sync the database schema:
```cmd
scripts\database-migration.bat
```
Or manually:
```cmd
cd backend
python -m alembic upgrade head
```

---

## 16. Running the Backend

Start the FastAPI application on `http://127.0.0.1:8000`:
```cmd
scripts\start-backend.bat
```
API Documentation (Swagger UI) is available at: `http://127.0.0.1:8000/docs`.

---

## 17. Running the Frontend

Start the React dashboard on `http://localhost:5173`:
```cmd
scripts\start-frontend.bat
```

---

## 18. Testing

Execute all 43 automated unit, database, and E2E simulation tests:
```cmd
python -m pytest backend/tests -v
```
To run the end-to-end simulation test (zero financial risk):
```cmd
python -m pytest backend/tests/unit/test_e2e_simulation.py -v
```
To verify the frontend production build:
```cmd
cd frontend
npm run build
```

---

## 19. Bot States

The engine implements a strict state machine:
* **`SYSTEM ONLINE`**: Backend is running, connected to MySQL, MT5 terminal monitored.
* **`TRADING ENABLED` (`RUNNING`)**: Signals are evaluated by Risk Engine and executed on MT5.
* **`TRADING PAUSED` (`PAUSED`)**: New signal entries are rejected; existing open positions are maintained.
* **`EMERGENCY STOP` (`EMERGENCY_STOP`)**: All incoming signals are blocked immediately; positions require manual or operator closure.

---

## 20. Trading Flow

1. **Signal Ingestion**: Webhook arrives at `POST /api/webhooks/tradingview`.
2. **Deduplication**: SHA-256 hash check prevents duplicate entries within 60 seconds.
3. **Signal Validation**: Validates symbol, action (`BUY`/`SELL`), and presence of mandatory Stop Loss.
4. **Session Check**: Verifies active trading window (`LONDON`, `NEW_YORK`) and current spread <= 35 points.
5. **Risk Validation**: Checks account balance, daily loss limit, open positions cap, and consecutive loss cooldown.
6. **Lot Calculation**: Computes deterministic position size based on dollar risk and tick specifications.
7. **Execution**: Dispatches market order via `IBrokerAdapter` to MT5 Vantage terminal.
8. **Persistence**: Saves `Order`, `Position`, and updates `Signal` status in MySQL.
9. **Notification**: Dispatches asynchronous Telegram alert.

---

## 21. Risk Management Engine

The Risk Engine operates independently with **final authority** over order execution:
* **`risk_per_trade`**: Maximum 1.0% account equity risked per trade.
* **`max_daily_loss`**: Circuit breaker triggers emergency pause if daily realized losses exceed 3.0%.
* **`max_open_positions`**: Hard ceiling of 2 concurrent open positions.
* **`max_consecutive_losses`**: 3 consecutive losses automatically pause the bot for 30 minutes.
* **`minimum_margin`**: Trading rejected if account margin level falls below 200%.
* **Mandatory Stop Loss**: Trades without a valid Stop Loss are rejected immediately.

---

## 22. Telegram Notifications

Outbound notification system configured in [`backend/app/notifications/telegram_bot.py`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/backend/app/notifications/telegram_bot.py):
* Alerts for: New signal, rejected signal, order submitted, order filled, position opened, position closed, profit/loss, risk rejection, daily loss reached, MT5 disconnected, database error, emergency stop, app startup, app shutdown.
* **Non-blocking & Fault-Tolerant**: If Telegram fails or returns HTTP errors, **trade execution is never interrupted**. Errors are logged safely.

---

## 23. Error Handling

* **Fail-Safe Uncertain Execution**: If MT5 returns an ambiguous network retcode (timeout, requote, 10004/10018), the order is marked `UNCERTAIN` and **never automatically retried**, preventing double fills.
* **Missing Data Rejection**: If symbol specs or account info cannot be fetched from the broker, the trade is rejected (no guessing).
* **Database Disconnects**: Operations caught in transit trigger transaction rollbacks, preventing partial records.

---

## 24. Logging

* Managed via **Loguru** with structured logs.
* Console outputs colorized logs with timestamps, log level, module, and message.
* Automated file log rotation at 20MB per log file in `logs/`.

---

## 25. Local Deployment

Detailed in [`docs/LOCAL_DEVELOPMENT.md`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/docs/LOCAL_DEVELOPMENT.md):
1. Start MySQL Server (`net start MySQL80`).
2. Launch MT5 Terminal and log in to Vantage Demo.
3. Run `scripts\start-backend.bat`.
4. Run `scripts\start-frontend.bat`.
5. Run `scripts\health-check.bat` to confirm `{"status": "healthy"}`.

---

## 26. VPS Deployment (24/7 Windows Server)

Detailed in [`docs/VPS_DEPLOYMENT.md`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/docs/VPS_DEPLOYMENT.md):
1. **Windows VPS**: Windows Server 2019/2022 (4 GB RAM, 2+ vCPUs, low latency to Vantage).
2. **NSSM Service**: Use [`deployment/vps/install_nssm_services.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/deployment/vps/install_nssm_services.bat) to install the backend as an auto-restarting Windows service with backoff throttle protection.
3. **Caddy HTTPS**: Run Caddy with [`deployment/vps/caddy_config.Caddyfile`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/deployment/vps/caddy_config.Caddyfile) for automatic TLS reverse proxy on port 443.
4. **MT5 Auto-Start**: Add MT5 shortcut to `shell:startup` for automatic startup on host reboot.

---

## 27. Database Backup

Run the automated backup script to create a timestamped SQL dump:
```cmd
scripts\database-backup.bat
```
Backups are saved to `backups\tradebot_db_YYYYMMDD_HHMM.sql`.

---

## 28. Database Restore

To restore from a backup file:
```cmd
mysql -u tradebot_user -p tradebot_db < backups\tradebot_db_YYYYMMDD_HHMM.sql
```

---

## 29. Troubleshooting

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `MT5 connection failed` | Terminal not running or Algo trading disabled | Launch MT5, enable Algo Trading button in top toolbar. |
| `MySQL Access Denied` | Incorrect credentials in `.env` | Verify `DB_USER` and `DB_PASSWORD` against MySQL instance. |
| `Signal Rejected: Spread Exceeded` | Market volatility or rollover hours | Normal behavior. Max spread cap protects capital. |
| `Port 8000 already in use` | Orphaned Uvicorn process | Run `scripts\stop-backend.bat`. |
| `Webhook Returns 401 Unauthorized` | Mismatched secret | Verify `X-Webhook-Secret` header matches `WEBHOOK_SECRET` in `.env`. |

---

## 30. Security Best Practices

* **No Public MySQL**: Port 3306 is bound strictly to `127.0.0.1` and never exposed to the public internet.
* **No Frontend Credentials**: Broker credentials, database passwords, and webhook secrets reside strictly in backend `.env` variables and are never bundled into React code.
* **Constant-Time Secret Comparison**: Webhook secrets are validated using `hmac.compare_digest` to prevent timing attacks.
* **Direct MT5 Isolation**: The React frontend communicates strictly via authenticated backend REST APIs; it never calls MT5 directly.

---

## 31. DEMO Mode

* Default runtime environment is `TRADING_ENV=DEMO`.
* The frontend header displays a high-visibility badge: `🛡️ DEMO MODE`.
* Connects to `VantageInternational-Demo`.
* If `MT5_LOGIN=0`, automatically defaults to the in-memory paper broker simulator.

---

## 32. LIVE Mode Transition

Transitioning to live money execution requires explicit intentional configuration:
1. Thoroughly paper-trade on Demo for at least 30 consecutive days.
2. In `.env`, change `TRADING_ENV=LIVE`.
3. Set `MT5_SERVER=VantageInternational-Live` and supply live MT5 account credentials.
4. Restart backend service. The frontend badge updates to `⚠️ LIVE REAL MONEY`.

---

## 33. Emergency Stop Procedure

If unexpected market behavior or platform divergence occurs:
1. Click **EMERGENCY STOP** on the top right of the dashboard.
2. Click **Yes** on the confirmation banner.
3. The backend transitions immediately to `EMERGENCY_STOP` state, blocking all new trade signals.
4. Telegram broadcasts an immediate critical alert.
5. Alternatively, trigger via API:
   ```cmd
   curl -X POST "http://127.0.0.1:8000/api/v1/control/emergency-stop?operator=MANUAL" -H "X-API-Key: YOUR_DASHBOARD_API_KEY"
   ```
