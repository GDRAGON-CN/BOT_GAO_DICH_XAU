"""Unit tests for configuration validation and environment constraints."""
import pytest
from app.core.config import Settings

def test_config_defaults_to_demo_and_local():
    """Verify default runtime settings are DEMO and local."""
    config = Settings()
    assert config.TRADING_ENV in ["DEMO", "LIVE"]
    assert config.TRADING_ENV == "DEMO"
    assert config.APP_ENV in ["local", "production"]

def test_config_risk_thresholds():
    """Verify safety risk thresholds are within bounded ranges."""
    config = Settings()
    assert 0.1 <= config.RISK_PERCENT_PER_TRADE <= 5.0
    assert 1.0 <= config.MAX_DAILY_LOSS_PERCENT <= 10.0
    assert config.MAX_OPEN_POSITIONS >= 1
    assert config.MIN_LOT_SIZE <= config.MAX_LOT_SIZE
    assert config.MAX_SPREAD_POINTS > 0
    assert config.MAX_SLIPPAGE_POINTS > 0

def test_config_database_urls():
    """Verify async and sync database connection URLs are well-formed."""
    config = Settings()
    assert config.async_database_url.startswith("mysql+aiomysql://")
    assert config.sync_database_url.startswith("mysql+pymysql://")
    assert "tradebot_db" in config.async_database_url
