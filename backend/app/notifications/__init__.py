"""Notifications package exports."""
from app.notifications.base import INotificationService
from app.notifications.message_templates import (
    format_emergency_stop,
    format_risk_rejection,
    format_trade_opened,
)
from app.notifications.telegram_bot import TelegramNotificationService, telegram_bot

__all__ = [
    "INotificationService",
    "TelegramNotificationService",
    "telegram_bot",
    "format_trade_opened",
    "format_risk_rejection",
    "format_emergency_stop",
]
