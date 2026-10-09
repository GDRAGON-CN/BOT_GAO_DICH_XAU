"""Trading session and spread validation service."""
from datetime import datetime, time, timezone
from typing import Optional, Tuple
from loguru import logger
# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.schemas.account import QuoteDTO

class TradingSessionService:
    """Validates forex/gold trading sessions and market spread."""

    SESSIONS = {
        "ASIAN": (time(0, 0), time(9, 0)),
        "LONDON": (time(7, 0), time(16, 0)),
        "NEW_YORK": (time(12, 0), time(21, 0)),
    }

    def is_session_active(self, current_utc_time: Optional[datetime] = None) -> Tuple[bool, str]:
        now = current_utc_time or datetime.now(timezone.utc)
        current_t = now.time()

        # Weekend market closures (Forex/Gold closed from Friday 22:00 UTC to Sunday 21:00 UTC)
        if now.weekday() == 5:
            return False, "MARKET_CLOSED_WEEKEND"
        if now.weekday() == 6 and current_t < time(21, 0):
            return False, "MARKET_CLOSED_WEEKEND"

        allowed = [s.upper() for s in settings.ALLOW_TRADING_SESSIONS]
        for name, (start, end) in self.SESSIONS.items():
            if name in allowed and start <= current_t <= end:
                return True, name

        return False, "OUTSIDE_ALLOWED_SESSIONS"

    def validate_spread(self, quote: Optional[QuoteDTO], max_spread_limit: Optional[float] = None) -> Tuple[bool, float, str]:
        if quote is None:
            return False, 0.0, "NO_QUOTE_AVAILABLE"

        limit = max_spread_limit if max_spread_limit is not None else settings.MAX_SPREAD_POINTS
        if quote.spread_points > limit:
            logger.warning(f"Spread exceeded: {quote.spread_points:.1f} > max {limit:.1f}")
            return False, quote.spread_points, f"Spread ({quote.spread_points:.1f}) exceeds maximum ({limit:.1f})"

        return True, quote.spread_points, "SPREAD_OK"

trading_session_service = TradingSessionService()
