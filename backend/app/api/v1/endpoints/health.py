from fastapi import APIRouter, Depends
from app.api.dependencies import get_broker
from app.brokers.base import IBrokerAdapter
from app.monitoring.health import HealthChecker

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def check_health(broker: IBrokerAdapter = Depends(get_broker)):
    checker = HealthChecker(broker)
    return await checker.check()
