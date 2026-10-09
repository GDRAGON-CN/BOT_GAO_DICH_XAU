import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import AsyncSessionLocal, engine
from app.models.audit import SystemSetting

async def seed():
    print("Seeding database system settings...")
    async with AsyncSessionLocal() as session:
        setting = SystemSetting(
            key_name="initial_setup",
            config_value={"initialized": True, "instrument": "XAUUSD"},
            description="Initial database configuration marker"
        )
        session.add(setting)
        await session.commit()
    print("Database seeded.")
    await engine.dispose()

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed())
