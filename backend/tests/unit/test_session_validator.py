from datetime import datetime, timezone
from app.schemas.account import QuoteDTO
from app.trading.session_validator import session_validator

def test_session_spread_validation():
    quote_ok = QuoteDTO(symbol="XAUUSD", bid=2650.0, ask=2650.2, spread_points=20.0, time=datetime.now(timezone.utc))
    valid, _, _ = session_validator.validate_spread(quote_ok)
    assert valid

    quote_bad = QuoteDTO(symbol="XAUUSD", bid=2650.0, ask=2650.5, spread_points=50.0, time=datetime.now(timezone.utc))
    valid_bad, _, _ = session_validator.validate_spread(quote_bad)
    assert not valid_bad
