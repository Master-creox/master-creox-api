from fastapi import APIRouter

from app.api.v1.endpoints import health, keys, models, tools

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(keys.router)
api_router.include_router(models.router)
api_router.include_router(tools.router)
