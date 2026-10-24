"""Developer Platform endpoints (Phase 5): self-service key management
and usage breakdown for the calling key."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.errors import APIError
from app.core.security import require_key

router = APIRouter(tags=["developer"])


class RotateKeyRequest(BaseModel):
    key_id: int


@router.get("/developer/me")
def developer_me(request: Request, key: dict = Depends(require_key)):
    keys = request.app.state.key_service.list_keys(user_id=key["user_id"])
    usage = request.app.state.usage_service.breakdown(
        user_id=key["user_id"], key_id=key["id"])
    return {"key_id": key["id"], "key_name": key["name"],
            "user_id": key["user_id"], "keys": keys, "usage": usage}


@router.post("/developer/keys/rotate", status_code=201)
def rotate_key(payload: RotateKeyRequest, request: Request,
               key: dict = Depends(require_key)):
    rotated = request.app.state.key_service.rotate_key(
        payload.key_id, user_id=key["user_id"], caller_key_id=key["id"])
    if rotated is None:
        raise APIError(404, "key_not_found",
                       "No active key with that id belongs to you.")
    return rotated


@router.get("/usage/breakdown")
def usage_breakdown(request: Request, key: dict = Depends(require_key)):
    return request.app.state.usage_service.breakdown(
        user_id=key["user_id"], key_id=key["id"])
