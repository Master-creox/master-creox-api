"""Admin controls (Phase 3): user list + platform stats. Admin key only."""
from fastapi import APIRouter, Depends, Request

from app.core.security import require_admin

router = APIRouter(tags=["admin"])


@router.get("/admin/users", dependencies=[Depends(require_admin)])
def list_users(request: Request):
    return {"users": request.app.state.user_service.list_users()}


@router.get("/admin/stats", dependencies=[Depends(require_admin)])
def platform_stats(request: Request):
    return request.app.state.usage_service.platform_stats()


@router.get("/admin/usage/recent", dependencies=[Depends(require_admin)])
def admin_recent_usage(request: Request, limit: int = 50):
    return {"recent": request.app.state.usage_service.recent_logs(limit=min(limit, 100))}
