"""Backward compatibility wrapper for RiskService."""
# pyrefly: ignore [missing-import]
from app.trading.risk_service import RiskService

class RiskEngine(RiskService):
    """Backward compatibility alias for RiskService."""
    pass
