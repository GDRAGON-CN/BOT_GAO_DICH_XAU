"""System Telemetry Tracker recording activity timestamps for health checks."""
from datetime import datetime, timezone
from typing import Optional

class SystemTelemetry:
    """Tracks timestamps of key events for health monitoring."""

    def __init__(self):
        self.last_webhook_received_at: Optional[datetime] = None
        self.last_successful_execution_at: Optional[datetime] = None
        self.last_account_sync_at: Optional[datetime] = None

    def record_webhook(self):
        self.last_webhook_received_at = datetime.now(timezone.utc)

    def record_execution(self):
        self.last_successful_execution_at = datetime.now(timezone.utc)

    def record_account_sync(self):
        self.last_account_sync_at = datetime.now(timezone.utc)

telemetry = SystemTelemetry()
