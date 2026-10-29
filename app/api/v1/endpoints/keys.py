"""Key management — admin (bootstrap key) or the owning user (JWT)."""
from fastapi import APIRouter, Depends, Request

from app.core.errors import APIError
from app.core.security import resolve_actor
from app.schemas.tools import CreateKeyRequest

router = APIRouter(tags=["keys"])


@router.post("/keys", status_code=201)
def create_key(payload: CreateKeyRequest, request: Request, actor=Depends(resolve_actor)):
    kind, user = actor
    created = request.app.state.key_service.create_key(
        payload.name, payload.scopes, user_id=user["id"] if user else None)
    request.app.state.audit_service.log(
        user["email"] if user else "admin", "key.create", f"key_id={created['id']} name={payload.name}")
    return created


@router.get("/keys")
def list_keys(request: Request, actor=Depends(resolve_actor)):
    kind, user = actor
    if kind == "admin":
        return {"keys": request.app.state.key_service.list_keys(admin=True)}
    return {"keys": request.app.state.key_service.list_keys(user_id=user["id"])}


@router.delete("/keys/{key_id}")
def revoke_key(key_id: int, request: Request, actor=Depends(resolve_actor)):
    kind, user = actor
    ok = request.app.state.key_service.revoke_key(
        key_id, user_id=user["id"] if user else None, admin=(kind == "admin"))
    if not ok:
        raise APIError(404, "key_not_found", "No active key with that id (or it is not yours).")
    request.app.state.audit_service.log(
        user["email"] if user else "admin", "key.revoke", f"key_id={key_id}")
    return {"revoked": key_id}


@router.get("/keys/{key_id}")
def key_detail(key_id: int, request: Request, actor=Depends(resolve_actor)):
    kind, user = actor
    keys = request.app.state.key_service.list_keys(admin=(kind == "admin"), user_id=user["id"] if user else None)
    row = next((k for k in keys if k["id"] == key_id), None)
    if row is None:
        raise APIError(404, "key_not_found", "No key with that id (or it is not yours).")
    usage = request.app.state.usage_service.breakdown(user_id=None, key_id=key_id)
    recent = request.app.state.usage_service.recent_logs(key_id=key_id, limit=50)
    return {"key": row, "usage": usage, "recent": recent}


@router.get("/keys/{key_id}/usage")
def key_usage(key_id: int, request: Request, actor=Depends(resolve_actor)):
    kind, user = actor
    keys = request.app.state.key_service.list_keys(admin=(kind == "admin"), user_id=user["id"] if user else None)
    if not any(k["id"] == key_id for k in keys):
        raise APIError(404, "key_not_found", "No key with that id (or it is not yours).")
    return {"key_id": key_id,
            "usage": request.app.state.usage_service.breakdown(user_id=None, key_id=key_id),
            "recent": request.app.state.usage_service.recent_logs(key_id=key_id, limit=100)}
