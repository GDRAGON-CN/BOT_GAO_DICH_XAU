"""FastAPI application factory and lifecycle orchestrator."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.api.dependencies import get_broker
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.base import Base
from app.database.session import engine
from app.monitoring.watchdog import TerminalWatchdog

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Gold Trading Engine [Env: {settings.APP_ENV}]...")
    from app.notifications.telegram_bot import telegram_bot
    telegram_bot.notify_app_startup(env=settings.APP_ENV, version="1.0.0")

    # 1. Database table sync
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database synchronized.")
    except Exception as e:
        logger.warning(f"MySQL connection warning: {e}. Running in decoupled mode.")
        telegram_bot.notify_database_error(str(e))

    # 2. Broker adapter initialization & Startup Reconciliation
    broker = get_broker()
    watchdog = TerminalWatchdog(broker)
    watchdog_task = None
    try:
        connected = await broker.initialize()
        if connected:
            logger.info("Broker initialization successful.")
            watchdog_task = asyncio.create_task(watchdog.start())

            # 3. Post-startup Reconciliation between Broker and DB
            try:
                from app.database.session import AsyncSessionLocal
                from app.trading.reconciliation_service import ReconciliationService
                async with AsyncSessionLocal() as db:
                    reconciler = ReconciliationService(broker)
                    await reconciler.run_reconciliation(db)
            except Exception as rec_err:
                logger.error(f"Post-startup reconciliation encountered error: {rec_err}")
        else:
            logger.warning("Broker adapter initialization returned False.")
            telegram_bot.notify_mt5_disconnected("Broker adapter initialization returned False")
    except Exception as e:
        logger.error(f"Broker startup error: {e}")
        telegram_bot.notify_mt5_disconnected(str(e))

    yield

    # Shutdown sequence
    logger.info("Shutting down Gold Trading Engine...")
    telegram_bot.notify_app_shutdown(env=settings.APP_ENV)
    if watchdog_task:
        watchdog.stop()
        watchdog_task.cancel()
    try:
        await broker.shutdown()
    except Exception as e:
        logger.error(f"Broker shutdown error: {e}")
    await engine.dispose()
    logger.info("Shutdown completed.")

app = FastAPI(
    title="XAUUSD Automated Gold Trading System",
    description="Production-grade trading automation linking TradingView, MT5, FastAPI, and MySQL.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.endpoints import webhook as webhook_endpoint

app.include_router(api_router, prefix="/api/v1")
app.include_router(webhook_endpoint.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "system": "XAUUSD Trading Engine",
        "env": settings.APP_ENV,
        "docs": "/docs"
    }
