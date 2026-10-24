"""Auth dependencies: API keys for clients, admin key, user JWT sessions."""
from __future__ import annotations

from fastapi import Header, Request

from app.core.config import settings
from app.core.errors import APIError
from app.services.token_service import decode_access_token


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


def get_current_user(request: Request, authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise APIError(401, "missing_token", "Authorization: Bearer <token> header is required.")
    payload = decode_access_token(authorization.split(" ", 1)[1].strip())
    user = request.app.state.user_service.get_by_id(int(payload["sub"]))
    if user is None:
        raise APIError(401, "invalid_token", "Token user no longer exists.")
    return user


def resolve_actor(request: Request,
                  x_admin_key: str | None = Header(default=None),
                  authorization: str | None = Header(default=None)) -> tuple[str, dict | None]:
    """Return ('admin', None) or ('user', user_dict) for key-management endpoints."""
    if settings.admin_key and x_admin_key and x_admin_key == settings.admin_key:
        return ("admin", None)
    if authorization and authorization.lower().startswith("bearer "):
        return ("user", get_current_user(request, authorization))
    if not settings.admin_key and not authorization:
        raise APIError(503, "admin_not_configured", "MASTER_CREOX_ADMIN_KEY is not set and no user token was provided.")
    raise APIError(401, "authentication_required", "Provide X-Admin-Key or a user Bearer token.")
