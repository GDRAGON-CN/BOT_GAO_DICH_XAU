"""Synthetic TradingView webhook sender for end-to-end integration testing."""
import json
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_SECRET = "tv_local_test_secret_123456"

def test_webhook_pipeline():
    print("Testing TradingView Webhook pipeline...")
    
    # 1. Check health
    try:
        res = httpx.get(f"{BASE_URL}/api/v1/health")
        print(f"Health Status: {res.status_code} -> {res.json()}")
    except Exception as e:
        print(f"Could not connect to {BASE_URL}. Ensure the backend is running. ({e})")
        return

    # 2. First resume the bot if paused
    headers = {"X-API-Key": "dash_local_secret_123456"}
    res = httpx.post(f"{BASE_URL}/api/v1/control/resume?operator=INTEGRATION_TEST", headers=headers)
    print(f"Resume Bot Response: {res.status_code} -> {res.json()}")

    # 3. Dispatch simulated BUY signal for XAUUSD
    payload = {
        "symbol": "XAUUSD",
        "action": "BUY",
        "timeframe": "M15",
        "price": 2650.00,
        "sl": 2645.00,
        "tp": 2660.00,
        "risk_percent": 1.0,
        "secret": WEBHOOK_SECRET,
        "bar_time": f"bar_{int(time.time())}"
    }

    webhook_headers = {"X-Webhook-Secret": WEBHOOK_SECRET}
    res = httpx.post(f"{BASE_URL}/api/v1/webhook/tradingview", json=payload, headers=webhook_headers)
    print(f"Webhook Signal Response: {res.status_code} -> {res.json()}")

    # 4. Check Dashboard Metrics
    metrics_res = httpx.get(f"{BASE_URL}/api/v1/dashboard/metrics")
    print(f"Dashboard Metrics: {metrics_res.status_code} -> Total Open Positions: {len(metrics_res.json().get('open_positions', []))}")

if __name__ == "__main__":
    test_webhook_pipeline()
