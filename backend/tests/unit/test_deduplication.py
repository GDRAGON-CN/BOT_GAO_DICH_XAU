from app.trading.deduplication import DeduplicationService

def test_deduplication_hashing():
    svc = DeduplicationService(ttl_seconds=5)
    payload = {"symbol": "XAUUSD", "action": "BUY", "timeframe": "M15", "bar_time": "2026-10-09T10:00:00"}
    h = svc.compute_hash(payload)
    
    is_dup, _ = svc.is_duplicate(h)
    assert not is_dup

    is_dup_retry, _ = svc.is_duplicate(h)
    assert is_dup_retry
