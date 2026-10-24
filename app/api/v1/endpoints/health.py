from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
        "api_version": settings.api_version,
        "environment": settings.environment,
    }
