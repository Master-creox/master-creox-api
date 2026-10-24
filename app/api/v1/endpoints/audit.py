"""Audit log viewer — admin only (Phase 2)."""
from fastapi import APIRouter, Depends, Request

from app.core.security import require_admin

router = APIRouter(tags=["admin"])


@router.get("/audit-logs", dependencies=[Depends(require_admin)])
def audit_logs(request: Request):
    return {"logs": request.app.state.audit_service.list_recent(50)}
