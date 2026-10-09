"""Async SQLAlchemy engine, connection pool resilience, and transaction management."""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from loguru import logger
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

# Engine with resilient connection pool configurations
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,       # Recycle connections every 30 minutes to prevent MySQL server-side timeout
    pool_pre_ping=True,      # Proactively test connection viability before checkout
    pool_timeout=30,         # Maximum seconds to wait for a pool connection before error
    connect_args={
        "connect_timeout": 10,  # TCP network connection timeout
        "read_default_group": "client"
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection yield for FastAPI routes with auto-cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            logger.error(f"Database session encountered error, rolled back: {exc}")
            raise
        finally:
            await session.close()

@asynccontextmanager
async def transaction_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for atomic database transactions.
    Ensures rollback on failure so no partial trade/order/signal state is left behind.
    Includes auto-reconnect retry logic for transient database disconnects.
    """
    max_retries = 3
    delay = 1.0

    for attempt in range(1, max_retries + 1):
        async with AsyncSessionLocal() as session:
            try:
                async with session.begin():
                    yield session
                return
            except (OperationalError, DBAPIError) as db_err:
                await session.rollback()
                if attempt < max_retries:
                    logger.warning(
                        f"Database connection error (attempt {attempt}/{max_retries}): {db_err}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Database transaction failed after {max_retries} attempts: {db_err}")
                    raise
            except Exception as exc:
                await session.rollback()
                logger.error(f"Transaction aborted and rolled back due to error: {exc}")
                raise

