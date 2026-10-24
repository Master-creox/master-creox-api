"""Usage statistics for the logged-in user (Phase 3)."""
from fastapi import APIRouter, Depends, Request

from app.core.security import get_current_user

router = APIRouter(tags=["usage"])


@router.get("/usage")
def my_usage(request: Request, user: dict = Depends(get_current_user)):
    stats = request.app.state.usage_service.stats_for_user(user["id"])
    return {"user_id": user["id"], **stats}
