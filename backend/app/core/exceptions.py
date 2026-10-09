"""Domain-specific exceptions for clean error categorization."""

class TradeBotError(Exception):
    """Base exception for all trading bot errors."""
    pass

class RiskViolationError(TradeBotError):
    """Raised when an incoming signal or order violates risk parameters."""
    def __init__(self, rule_name: str, message: str):
        self.rule_name = rule_name
        self.message = message
        super().__init__(f"Risk Violation [{rule_name}]: {message}")

class BrokerConnectionError(TradeBotError):
    """Raised when the broker adapter cannot communicate with MT5 terminal."""
    pass

class OrderExecutionError(TradeBotError):
    """Raised when the broker rejects an order or returns an execution error."""
    def __init__(self, retcode: int, message: str):
        self.retcode = retcode
        self.message = message
        super().__init__(f"Order Execution Failed (retcode: {retcode}): {message}")

class DuplicateSignalError(TradeBotError):
    """Raised when an identical signal payload is received in the sliding deduplication window."""
    pass

class InactiveSessionError(TradeBotError):
    """Raised when an order signal arrives outside permitted trading hours or during market closures."""
    pass
