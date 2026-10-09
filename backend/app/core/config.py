"""Configuration loader merging .env and YAML config files."""
import json
import os
from pathlib import Path
from typing import Dict, List, Literal, Optional
import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config"

def load_yaml(filename: str) -> dict:
    file_path = CONFIG_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Runtime Environment
    APP_ENV: Literal["local", "production"] = "local"
    DEBUG: bool = True
    TRADING_ENV: Literal["DEMO", "LIVE"] = "DEMO"  # Always defaults to DEMO/PAPER. Never live.


    # Server Configuration
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database Configuration (MySQL 8+)
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "tradebot_db"

    # MetaTrader 5 Broker Configuration
    MT5_PATH: Optional[str] = None
    MT5_LOGIN: int = 0
    MT5_PASSWORD: str = ""
    MT5_SERVER: str = "VantageInternational-Demo"
    MT5_TIMEOUT_MS: int = 10000

    # Symbol Configuration
    DEFAULT_SYMBOL: str = "XAUUSD"
    BROKER_SYMBOL_MAP: Dict[str, str] = Field(default_factory=lambda: {"XAUUSD": "XAUUSD"})

    # Security Credentials
    WEBHOOK_SECRET: str = "tv_local_test_secret_123456"
    DASHBOARD_API_KEY: str = "dash_local_secret_123456"

    # Risk Engine Rules
    RISK_PERCENT_PER_TRADE: float = 1.0
    MAX_DAILY_LOSS_PERCENT: float = 3.0
    MAX_OPEN_POSITIONS: int = 2
    MAX_LOT_SIZE: float = 1.00
    MIN_LOT_SIZE: float = 0.01
    MAX_SPREAD_POINTS: float = 35.0
    MAX_SLIPPAGE_POINTS: float = 20.0
    MAX_CONSECUTIVE_LOSSES: int = 3
    COOLDOWN_MINUTES_AFTER_LOSS: int = 30
    ALLOW_TRADING_SESSIONS: List[str] = ["LONDON", "NEW_YORK", "ASIAN"]

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_ENABLE_ALERTS: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("BROKER_SYMBOL_MAP", mode="before")
    @classmethod
    def parse_symbol_map(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {"XAUUSD": "XAUUSD"}
        return v

    @property
    def async_database_url(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def sync_database_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

settings = Settings()
