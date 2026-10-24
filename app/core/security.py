"""Auth dependencies: API keys for clients, admin key for key management."""
from __future__ import annotations

from fastapi import Depends, Header, Request

from app.core.config import settings
from app.core.errors import APIError


def get_key_service(request: Request):
    return request.app.state.key_service


def require_scope(scope: str):
    async def _dep(request: Request, x_api_key: str | None = Header(default=None)):
        if not x_api_key:
            raise APIError(401, "missing_api_key", "X-API-Key header is required.")
        record = request.app.state.key_service.verify(x_api_key, scope)
        if record is None:
            raise APIError(401, "invalid_api_key", "API key is invalid, revoked, or lacks the required scope.")
        return record

    return _dep


async def require_admin(x_admin_key: str | None = Header(default=None)):
    if not settings.admin_key:
        raise APIError(503, "admin_not_configured", "Key management is disabled: MASTER_CREOX_ADMIN_KEY is not set on the server.")
    if x_admin_key != settings.admin_key:
        raise APIError(401, "invalid_admin_key", "X-Admin-Key header is missing or invalid.")
    return True
