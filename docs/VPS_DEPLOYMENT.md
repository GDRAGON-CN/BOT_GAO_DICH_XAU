# Windows VPS 24/7 Production Deployment Guide

This document specifies the exact architecture, prerequisites, and step-by-step procedures to migrate the **XAUUSD Automated Gold Trading System** from a local Windows environment to a dedicated **Windows VPS** for uninterrupted 24/7 execution.

> [!IMPORTANT]
> **No Application Logic Rewriting**: The core codebase remains identical between local development and VPS production. Only configuration (`.env`), reverse proxy, and process management change.

---

## 1. System & Hardware Specifications

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **Operating System** | Windows Server 2019 / 2022 (64-bit) | Windows Server 2022 Standard |
| **CPU** | 2 vCPU cores (2.4 GHz+) | 4 vCPU cores (3.0 GHz+) |
| **RAM** | 4 GB RAM | 8 GB RAM |
| **Disk Storage** | 40 GB SSD / NVMe | 80 GB NVMe SSD |
| **Network** | 100 Mbps port, low latency to Vantage | Low-latency location (e.g. London / New York LD4/NY4) |
| **Uptime / SLA** | 99.9% uptime | 99.99% with automated host failover |

---

## 2. Required Software on Windows VPS

1. **Python**: 3.10 or 3.11 64-bit (Add to Windows `PATH`).
2. **Git for Windows**: For cloning and updating repository.
3. **MySQL Server 8.0+**: Configured locally, listening **only** on `127.0.0.1:3306`.
4. **MySQL Workbench**: For administrative queries (connects locally or via SSH tunnel).
5. **MetaTrader 5 Terminal**: Vantage 64-bit client (`terminal64.exe`).
6. **Reverse Proxy (HTTPS)**: [Caddy Server for Windows](https://caddyserver.com/) (Auto SSL via Let's Encrypt) or Nginx.
7. **Service Supervisor**: [NSSM (Non-Sucking Service Manager)](https://nssm.cc/) to run the backend as a resilient Windows Service.

---

## 3. Architecture & Security Layout

```
TradingView Alert (Internet)
       ↓  (HTTPS Port 443)
[Windows Firewall / Caddy Reverse Proxy]
       ↓  (HTTP Port 8000 via 127.0.0.1)
[FastAPI Python Backend] (Runs as Windows Service via NSSM)
   ├── MySQL 8+ (127.0.0.1:3306 - NEVER EXPOSED PUBLICLY)
   └── MetaTrader 5 Terminal (Vantage Demo/Live via Windows IPC)
```

### Security Rules:
* **MySQL is Strictly Private**: Port 3306 is **never** opened in the Windows Firewall or forwarded to the public internet. Only the backend process connects to `127.0.0.1:3306`.
* **Database Administration**: Connect to MySQL Workbench directly on the VPS desktop via Remote Desktop (RDP) or through an encrypted SSH tunnel.
* **Public Webhook Endpoint**: Only `POST /api/webhooks/tradingview` is exposed externally behind TLS 1.3 reverse proxy (`https://tradebot.yourdomain.com`).
* **Authentication**: Every incoming alert must validate the secret token against `WEBHOOK_SECRET`.

---

## 4. End-to-End Migration & Setup Sequence

### Phase 1: Clone Repository & Python Environment
1. Open PowerShell on the VPS and clone the repository:
   ```cmd
   git clone https://github.com/your-repo/bot-trading.git C:\tradebot
   cd C:\tradebot
   ```
2. Create and activate a Python virtual environment:
   ```cmd
   python -m venv venv
   call venv\Scripts\activate.bat
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Phase 2: Configure Production `.env`
Copy `.env.example` to `.env`:
```cmd
copy .env.example .env
```
Update production settings:
```ini
APP_ENV=production
DEBUG=false
TRADING_ENV=DEMO

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Private Database
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=tradebot_admin
DB_PASSWORD=A_VERY_STRONG_PASSWORD_HERE
DB_NAME=tradebot_db

# MT5 Terminal Configuration
MT5_LOGIN=YOUR_VANTAGE_ACCOUNT_NUMBER
MT5_PASSWORD=YOUR_VANTAGE_PASSWORD
MT5_SERVER=VantageInternational-Demo
MT5_PATH=C:\Program Files\Vantage MetaTrader 5\terminal64.exe

# Security
WEBHOOK_SECRET=YOUR_COMPLEX_RANDOM_WEBHOOK_SECRET
DASHBOARD_API_KEY=YOUR_COMPLEX_DASHBOARD_SECRET

# Telegram Alerts
TELEGRAM_ENABLE_ALERTS=true
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
```

### Phase 3: Setup MySQL & Restore Database
1. In MySQL Command Line or Workbench:
   ```sql
   CREATE DATABASE tradebot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'tradebot_admin'@'127.0.0.1' IDENTIFIED BY 'A_VERY_STRONG_PASSWORD_HERE';
   GRANT ALL PRIVILEGES ON tradebot_db.* TO 'tradebot_admin'@'127.0.0.1';
   FLUSH PRIVILEGES;
   ```
2. Apply database migrations:
   ```cmd
   python -m alembic upgrade head
   ```
   *(Or restore existing backup: `mysql -u tradebot_admin -p tradebot_db < C:\tradebot\backups\tradebot_db_backup.sql`)*

### Phase 4: Install & Configure Vantage MetaTrader 5
1. Install Vantage MT5 to `C:\Program Files\Vantage MetaTrader 5\`.
2. Launch MT5 and log in with your demo credentials (or live account when approved).
3. Under `Tools -> Options -> Expert Advisors`:
   * Check **Allow algorithmic trading**.
   * Check **Allow DLL imports**.
4. Configure Windows Auto-Logon for MT5:
   * Place an MT5 shortcut in the Windows Startup folder:
     `shell:startup` (`C:\Users\<User>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`)
   * MT5 will automatically start whenever the VPS boots up.

### Phase 5: Expose Public HTTPS Webhook via Caddy
1. Download [Caddy for Windows](https://caddyserver.com/) to `C:\caddy\caddy.exe`.
2. Configure `C:\tradebot\deployment\vps\caddy_config.Caddyfile`:
   ```caddy
   tradebot.yourdomain.com {
       handle /api/* {
           reverse_proxy 127.0.0.1:8000
       }
       handle {
           root * C:\tradebot\frontend\dist
           file_server
           try_files {path} /index.html
       }
   }
   ```
3. Point your DNS A-Record (`tradebot.yourdomain.com`) to your VPS Static Public IP.
4. Open ports **80** and **443** in Windows Firewall:
   ```cmd
   netsh advfirewall firewall add rule name="Caddy HTTP" dir=in action=allow protocol=TCP localport=80
   netsh advfirewall firewall add rule name="Caddy HTTPS" dir=in action=allow protocol=TCP localport=443
   ```
5. Install Caddy as a Windows service:
   ```cmd
   caddy.exe start --config C:\tradebot\deployment\vps\caddy_config.Caddyfile
   ```

---

## 5. 24/7 Resilience & Self-Healing Strategy

The system is engineered to recover automatically from any single-point failure without operator intervention:

### 1. Backend Process Crash
* **Mechanism**: NSSM monitors the Python process.
* **Auto-Restart**: Automatically restarts the backend within 5 seconds (`AppRestartDelay 5000`).
* **Anti-Infinite Loop**: NSSM throttle protection (`AppThrottle 15000`) pauses restart attempts if the process crashes continuously within 15 seconds, preventing CPU exhaustion.
* **Log Retention**: All stdout/stderr is logged to `C:\tradebot\logs\backend_service_stderr.log` with 20MB file rotation.

### 2. MT5 Terminal Restart
* **Mechanism**: Handled by [watchdog.py](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/backend/app/monitoring/watchdog.py).
* **Protective Action**: The watchdog polls MT5 connection status every 30 seconds.
* **Failsafe**: If MT5 disconnects while trading is active, the bot transitions immediately to `PAUSED` and dispatches a Telegram alert.
* **Reconnection**: When MT5 becomes reachable again, [reconciliation_service.py](file:///d:/BOT%20Giao%20d%E1%BB%8Bch/backend/app/trading/reconciliation_service.py) automatically resynchronizes open positions between broker terminal and database.

### 3. Windows VPS Reboot (e.g. Windows Updates)
* **Startup Sequence**:
  1. Windows boots.
  2. MySQL Service starts automatically (`SERVICE_AUTO_START`).
  3. NSSM starts `XAUUSD_Backend` Windows Service.
  4. Auto-logon launches MetaTrader 5 Terminal.
  5. Backend startup sequence runs table check and **post-startup reconciliation**, logging any positions closed while the host was restarting.
  6. Telegram notification confirms application startup.

### 4. Temporary Network Drop
* **Trading Engine Safety**: All pending orders have fixed Stop Loss sent directly to MT5. If internet drops, Vantage broker server holds the hard SL server-side.
* **Webhook Retry**: TradingView retries alert delivery if the network packet drops.

---

## 6. Automated Backup Strategy

To ensure zero data loss, schedule daily automated backups using Windows Task Scheduler:

1. Open **Task Scheduler** (`taskschd.msc`).
2. Create a Basic Task: `TradeBot_Daily_Backup`.
3. Trigger: **Daily at 00:05 UTC**.
4. Action: Start a Program:
   * Program: `cmd.exe`
   * Arguments: `/c C:\tradebot\scripts\database-backup.bat`
5. Backups are stored in `C:\tradebot\backups\` with timestamped file names (`tradebot_db_YYYYMMDD_HHMM.sql`).
