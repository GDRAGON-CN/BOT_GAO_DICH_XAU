import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_SECRET = "tv_local_test_secret_123456"

def test_webhook_pipeline():
    print("Testing TradingView Webhook pipeline...")
    
    # 1. Health probe
    try:
        res = httpx.get(f"{BASE_URL}/api/v1/health")
        print(f"Health Status: {res.status_code} -> {res.json()}")
    except Exception as e:
        print(f"Could not connect to backend at {BASE_URL}. Ensure it is running. ({e})")
        return

    # 2. Resume bot
    headers = {"X-API-Key": "dash_local_secret_123456"}
    res = httpx.post(f"{BASE_URL}/api/v1/control/resume?operator=INTEGRATION_TEST", headers=headers)
    print(f"Resume Bot: {res.status_code} -> {res.json()}")

    # 3. Send BUY signal
    payload = {
        "event_id": f"evt_{int(time.time())}",
        "symbol": "XAUUSD",
        "action": "BUY",
        "timeframe": "M15",
        "entry": 2650.00,
        "price": 2650.00,
        "stop_loss": 2645.00,
        "sl": 2645.00,
        "take_profit": 2660.00,
        "tp": 2660.00,
        "risk_percent": 1.0,
        "strategy": "gold_m15_v1",
        "timestamp": str(int(time.time())),
        "secret": WEBHOOK_SECRET
    }

    webhook_headers = {"X-Webhook-Secret": WEBHOOK_SECRET}
    res = httpx.post(f"{BASE_URL}/api/webhooks/tradingview", json=payload, headers=webhook_headers)
    print(f"Signal Result: {res.status_code} -> {res.text}")

    # Allow background execution worker to process
    time.sleep(1.0)

    # 4. Fetch metrics
    metrics_res = httpx.get(f"{BASE_URL}/api/v1/dashboard/metrics")
    if metrics_res.status_code == 200:
        metrics = metrics_res.json()
        print(f"Active Positions: {len(metrics.get('open_positions', []))}")
    else:
        print(f"Metrics query returned {metrics_res.status_code}")

if __name__ == "__main__":
    test_webhook_pipeline()
