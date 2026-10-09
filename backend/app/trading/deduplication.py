import hashlib
import json
import time
from typing import Dict, Tuple
from loguru import logger

class DeduplicationService:
    """Sliding-window fingerprint detector for duplicate signals."""

    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, float] = {}

    def compute_hash(self, payload: dict) -> str:
        canonical = {
            "symbol": str(payload.get("symbol", "")).upper().strip(),
            "action": str(payload.get("action", "")).upper().strip(),
            "timeframe": str(payload.get("timeframe", "")).strip(),
            "bar_time": str(payload.get("bar_time", "")).strip(),
            "price": str(payload.get("price", "")).strip(),
        }
        serialized = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def is_duplicate(self, payload_hash: str) -> Tuple[bool, float]:
        now = time.time()
        self._purge_expired(now)

        if payload_hash in self._cache:
            elapsed = now - self._cache[payload_hash]
            logger.warning(f"Duplicate signal detected in memory: {payload_hash[:10]}... ({elapsed:.1f}s ago)")
            return True, elapsed

        self._cache[payload_hash] = now
        return False, 0.0

    def record_seen(self, payload_hash: str):
        self._cache[payload_hash] = time.time()

    def _purge_expired(self, now: float):
        expired = [h for h, ts in self._cache.items() if now - ts > self.ttl_seconds]
        for h in expired:
            del self._cache[h]

deduplication_service = DeduplicationService()

