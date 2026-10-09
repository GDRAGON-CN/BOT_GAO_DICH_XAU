# Local Windows Development Guide (No Docker Required)

This document provides the exact end-to-end setup and operation sequence for the **XAUUSD Automated Gold Trading System** on Windows.

---

## 1. Required Local Services

| Component | Software | Local Requirement | Default Port / Connection |
| :--- | :--- | :--- | :--- |
| **Database** | MySQL Server 8.0+ | Windows Service running (`MySQL80`) | `127.0.0.1:3306` (`tradebot_db`) |
| **DB Admin** | MySQL Workbench | Visual schema inspection and debugging | GUI Connection to `127.0.0.1:3306` |
| **Backend** | Python 3.10+ / FastAPI | Local Python with Uvicorn | `http://127.0.0.1:8000` |
| **Frontend** | Node.js 18+ / React / Vite | Local Vite dev server | `http://localhost:5173` |
| **Broker Bridge**| MetaTrader 5 Terminal | Windows 64-bit MT5 desktop application | Vantage Demo Terminal (`terminal64.exe`) |
| **Account** | Vantage MT5 Demo Account | Demo credentials (Never live) | Server: `VantageInternational-Demo` |

---

## 2. Safety First: DEMO Mode Verification

> [!IMPORTANT]
> The system defaults strictly to **DEMO MODE**.
> * The frontend header displays a high-visibility badge: `🛡️ DEMO MODE`.
> * The backend `.env` must define `TRADING_ENV=DEMO`.
> * Never set `TRADING_ENV=LIVE` on local development workstations.
> * The system will **never silently connect** to a live money account.

---

## 3. Step-by-Step Local Startup Sequence

Follow these 11 steps in exact sequence:

### Step 1: Start MySQL Server
Ensure the MySQL Windows Service is active:
1. Open PowerShell / Command Prompt as Administrator, or open **Services** (`services.msc`).
2. Verify or start MySQL:
   ```cmd
   net start MySQL80
   ```

### Step 2: Verify Database via MySQL Workbench
1. Launch **MySQL Workbench**.
2. Connect to Local instance (`root` on `127.0.0.1:3306`).
3. Ensure schema `tradebot_db` exists:
   ```sql
   CREATE DATABASE IF NOT EXISTS tradebot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   USE tradebot_db;
   SHOW TABLES;
   ```
4. If setting up for the first time, run the database migration:
   * Double-click `scripts\database-migration.bat` or run:
     ```cmd
     python -m alembic upgrade head
     ```

### Step 3: Start MetaTrader 5 Terminal
1. Launch **MetaTrader 5** from the Windows Start menu or desktop shortcut.
2. Ensure **Algo Trading** (Automated Trading) is enabled in the MT5 top toolbar (Green Play icon).
3. Under MT5 `Tools -> Options -> Expert Advisors`:
   * Check **Allow algorithmic trading**.
   * Check **Allow DLL imports**.

### Step 4: Login to Vantage MT5 Demo Account
1. In MT5, click `File -> Login to Trade Account`.
2. Enter your Demo login credentials:
   * **Login**: Your Vantage Demo Account Number
   * **Password**: Your Demo Trader Password
   * **Server**: `VantageInternational-Demo`
3. Verify connection sound and look for the green connection status indicator in the bottom-right corner of MT5.

### Step 5: Start Python FastAPI Backend
1. Double-click `scripts\start-backend.bat` or run:
   ```cmd
   python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```
2. The backend connects to the database, initializes the broker adapter, checks MT5 status, and starts the watchdog daemon.

### Step 6: Start React Frontend Dashboard
1. Double-click `scripts\start-frontend.bat` or run:
   ```cmd
   cd frontend
   npm run dev
   ```
2. Open your browser at `http://localhost:5173`.
3. Verify that the UI header clearly shows `🛡️ DEMO MODE` and `SYSTEM ONLINE` / `TRADING PAUSED`.

### Step 7: Verify System Health
Run the health check script to probe all subsystems:
* Double-click `scripts\health-check.bat` or browse to `http://127.0.0.1:8000/api/v1/health`.
* Expected JSON response:
  ```json
  {
    "status": "healthy",
    "environment": "local",
    "bot_state": "PAUSED",
    "components": {
      "backend": { "status": "healthy" },
      "mysql": { "status": "healthy" },
      "mt5": { "status": "connected", "broker": "Vantage MT5", "connected": true }
    }
  }
  ```

### Step 8: Test TradingView Webhook Endpoint
Ensure the webhook listener is responding:
```cmd
python -c "import httpx; print(httpx.get('http://127.0.0.1:8000/api/v1/health').status_code)"
```

### Step 9: Test Signal Pipeline
Run the included end-to-end simulation script:
* Double-click `scripts\test-pipeline.bat` or execute:
  ```cmd
  python backend\scripts\test_webhook.py
  ```
* This simulates an authenticated TradingView payload sent to `/api/webhooks/tradingview`.

### Step 10: Test Risk Management Engine
* On the frontend dashboard (`http://localhost:5173`), click **START TRADING** and confirm.
* Send a test signal using `test_webhook.py`.
* Check the dashboard or run tests:
  ```cmd
  python -m pytest backend/tests/unit/test_risk_management_engine.py -v
  ```
* Verify that spread, position caps, and lot sizing are evaluated deterministically.

### Step 11: Test MT5 Demo Execution
* Confirm the order appears in your Vantage MT5 Terminal **Trade** tab.
* Confirm the executed position ticket, lot size, and entry price sync to the **Open Positions** table on `http://localhost:5173`.
* Verify that the database stores the audit record in MySQL Workbench (`SELECT * FROM orders;`).

---

## 4. Windows Helper Scripts (`scripts\`)

All operations are executable with standard Windows Command Prompt / Batch scripts (no Linux/Bash commands required):

| Script | Purpose |
| :--- | :--- |
| [`scripts\start-backend.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/scripts/start-backend.bat) | Starts FastAPI backend server with Uvicorn on port 8000. |
| [`scripts\stop-backend.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/scripts/stop-backend.bat) | Safely stops any running backend process on port 8000. |
| [`scripts\start-frontend.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/scripts/start-frontend.bat) | Starts the React Vite development server on port 5173. |
| [`scripts\health-check.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/scripts/health-check.bat) | Probes backend, MySQL, and MT5 connectivity and outputs JSON. |
| [`scripts\database-migration.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/scripts/database-migration.bat) | Applies Alembic migrations (`python -m alembic upgrade head`). |
| [`scripts\database-backup.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/scripts/database-backup.bat) | Creates a timestamped `.sql` backup file using `mysqldump`. |
| [`scripts\test-pipeline.bat`](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/scripts/test-pipeline.bat) | Triggers test webhook signal and inspects real-time execution. |

---

## 5. Troubleshooting Common Local Issues

* **MySQL `Access Denied`**:
  * Verify user and password in `.env` match your MySQL setup (`DB_USER=root`, `DB_PASSWORD=...`).
* **MT5 Connection Fails (`MT5 initialization failed`)**:
  * Make sure MetaTrader 5 terminal is open on Windows.
  * Check that `MT5_LOGIN` and `MT5_SERVER` in `.env` match your Vantage demo account.
  * If testing without live MT5, setting `MT5_LOGIN=0` runs the built-in paper broker simulator.
* **Port 8000 or 5173 Already in Use**:
  * Run `scripts\stop-backend.bat` to terminate orphaned processes.
