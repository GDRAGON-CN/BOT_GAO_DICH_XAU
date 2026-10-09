"""Timestamp validation utility with strict parsing and tolerance window checking."""
from datetime import datetime, timezone
from typing import Optional, Tuple
from loguru import logger
from app.core.config import settings

class TimestampValidator:
    """
    Validates TradingView alert timestamps.
    Supports:
    - Unix timestamp in seconds (e.g. 1770000000 or "1770000000")
    - Unix timestamp in milliseconds (e.g. 1770000000000 or "1770000000000")
    - ISO 8601 strings (e.g. "2026-10-09T11:00:00Z" or "2026-10-09T11:00:00+00:00")
    Rejects malformed timestamps and stale alerts exceeding configured tolerance.
    """

    @classmethod
    def parse_timestamp(cls, raw_val: Optional[str]) -> Tuple[bool, Optional[datetime], Optional[str]]:
        """
        Parses raw timestamp into a timezone-aware UTC datetime.
        Returns: (is_valid, parsed_dt_utc, error_message)
        """
        if not raw_val or not str(raw_val).strip():
            return False, None, "Timestamp is missing or empty"

        raw_str = str(raw_val).strip()

        # 1. Numeric Unix timestamp (seconds or milliseconds)
        try:
            # Check if float or int representation
            numeric_val = float(raw_str)
            # If greater than 1e11, it's milliseconds
            if numeric_val > 1e11:
                numeric_val = numeric_val / 1000.0
            dt = datetime.fromtimestamp(numeric_val, tz=timezone.utc)
            return True, dt, None
        except (ValueError, OverflowError):
            pass

        # 2. ISO 8601 string
        try:
            # Handle trailing Z
            iso_str = raw_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                # If naive, assume UTC as per spec
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return True, dt, None
        except Exception:
            pass

        return False, None, f"Malformed timestamp '{raw_val}'. Expected Unix epoch (s/ms) or ISO 8601 string."

    @classmethod
    def validate_freshness(
        cls,
        raw_val: Optional[str],
        tolerance_seconds: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates both timestamp formatting and timeliness.
        Fails closed on any parse error or if drift exceeds tolerance.
        """
        if tolerance_seconds is None:
            tolerance_seconds = settings.ALERT_TIMESTAMP_TOLERANCE_SECONDS

        is_valid, dt_utc, err = cls.parse_timestamp(raw_val)
        if not is_valid or dt_utc is None:
            return False, err

        now_utc = datetime.now(timezone.utc)
        drift = abs((now_utc - dt_utc).total_seconds())

        if drift > tolerance_seconds:
            msg = (
                f"Stale signal timestamp: alert time ({dt_utc.isoformat()}) "
                f"differs from server time ({now_utc.isoformat()}) by {drift:.1f}s "
                f"(max tolerance: {tolerance_seconds}s)."
            )
            logger.warning(msg)
            return False, msg

        return True, None
