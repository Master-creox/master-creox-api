"""Key management — admin only (bootstrap admin key from environment)."""
from fastapi import APIRouter, Depends, Request

from app.core.errors import APIError
from app.core.security import require_admin
from app.schemas.tools import CreateKeyRequest

router = APIRouter(tags=["keys"])


@router.post("/keys", dependencies=[Depends(require_admin)], status_code=201)
def create_key(payload: CreateKeyRequest, request: Request):
    return request.app.state.key_service.create_key(payload.name, payload.scopes)


@router.get("/keys", dependencies=[Depends(require_admin)])
def list_keys(request: Request):
    return {"keys": request.app.state.key_service.list_keys()}


@router.delete("/keys/{key_id}", dependencies=[Depends(require_admin)])
def revoke_key(key_id: int, request: Request):
    if not request.app.state.key_service.revoke_key(key_id):
        raise APIError(404, "key_not_found", "No active key with that id.")
    return {"revoked": key_id}
