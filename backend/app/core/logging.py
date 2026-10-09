"""Structured logging with secret redaction and daily file rotation."""
import re
import sys
from loguru import logger
from app.core.config import settings

SENSITIVE_PATTERNS = [
    re.compile(r"(password=)['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"(token=)['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"(secret=)['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"(bot[0-9]+:[a-zA-Z0-9_-]+)", re.IGNORECASE),
]

def mask_sensitive_data(message: str) -> str:
    masked = message
    for pattern in SENSITIVE_PATTERNS:
        masked = pattern.sub(r"\1[REDACTED]", masked)
    return masked

def filter_record(record):
    record["message"] = mask_sensitive_data(record["message"])
    return True

def setup_logging():
    logger.remove()
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        filter=filter_record,
        colorize=True,
    )
    
    logger.add(
        "logs/trading_{time:YYYY-MM-DD}.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        filter=filter_record,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )

    return logger
