from fastapi import APIRouter

from app.api.v1.endpoints import audit, auth, health, keys, models, tools

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(keys.router)
api_router.include_router(models.router)
api_router.include_router(tools.router)
api_router.include_router(audit.router)
