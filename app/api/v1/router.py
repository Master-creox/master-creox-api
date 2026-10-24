from fastapi import APIRouter

from app.api.v1.endpoints import admin, audit, auth, chat, developer, health, keys, models, tools, usage

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(keys.router)
api_router.include_router(models.router)
api_router.include_router(chat.router)
api_router.include_router(developer.router)
api_router.include_router(tools.router)
api_router.include_router(usage.router)
api_router.include_router(admin.router)
api_router.include_router(audit.router)
