"""User registration, login (JWT) and profile (Phase 2)."""
from fastapi import APIRouter, Depends, Request

from app.core.config import settings
from app.core.errors import APIError
from app.core.security import get_current_user
from app.schemas.auth import RegisterRequest, TokenRequest, TokenResponse
from app.services.token_service import create_access_token

router = APIRouter(tags=["auth"])


@router.post("/auth/register", status_code=201)
def register(payload: RegisterRequest, request: Request):
    user = request.app.state.user_service.register(payload.name, payload.email, payload.password)
    request.app.state.audit_service.log(user["email"], "user.register", f"user_id={user['id']}")
    return user


@router.post("/auth/token", response_model=TokenResponse)
def login(payload: TokenRequest, request: Request):
    user = request.app.state.user_service.authenticate(payload.email, payload.password)
    if user is None:
        request.app.state.audit_service.log(payload.email.lower(), "auth.login_failed", "")
        raise APIError(401, "invalid_credentials", "Email or password is incorrect.")
    request.app.state.audit_service.log(user["email"], "auth.login", f"user_id={user['id']}")
    return TokenResponse(
        access_token=create_access_token(user),
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user
