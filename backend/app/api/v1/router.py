from fastapi import APIRouter
from app.api.v1.endpoints import control, dashboard, health, webhook

api_router = APIRouter()
api_router.include_router(webhook.router)
api_router.include_router(control.router)
api_router.include_router(dashboard.router)
api_router.include_router(health.router)
