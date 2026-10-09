# Architecture & System Design Specification

## Overview
The Personal Automated Gold Trading System is engineered for sub-5ms local order execution on Windows, connecting TradingView Pine Script alerts to MetaTrader 5 (Vantage Markets) via an asynchronous, decoupled FastAPI engine and MySQL 8+ database.

## System Topology & Layers
```
TradingView Alert Engine
        │ HTTPS Webhook (X-Webhook-Secret)
        ▼
Presentation Layer (FastAPI)
        │ Payload Validation & Rate Limiting
        ▼
Deduplication & Ingestion (Sliding Window SHA-256)
        │
        ▼
Session & Spread Validator (London / NY / Spread limits)
        │
        ▼
Risk Gating Engine (Circuit Breakers, Equity %, Sizing)
        │
        ▼
Position Manager (Idempotency & Ticket Rebalancing)
        │
        ▼
Broker Abstraction (IBrokerAdapter)
        │
        ▼
MetaTrader 5 Adapter (MT5 Win32 SDK)
        │
        ▼
Vantage Markets Server (XAUUSD Execution)
```

## Fault Isolation
* The trading core depends exclusively on the `IBrokerAdapter` abstraction.
* If MT5 terminal IPC disconnects, `TerminalWatchdog` transitions the system into `PAUSED` mode and notifies Telegram.
* Under extreme volatility, spread spikes exceeding `MAX_SPREAD_POINTS` abort the entry immediately.
