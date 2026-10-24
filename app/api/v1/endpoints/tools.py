"""Tool endpoints built from Akash's own projects (ai-cyber-account-lab)."""
from fastapi import APIRouter, Depends

from app.core.security import require_scope
from app.schemas.tools import (
    PasswordCheckRequest,
    PasswordCheckResponse,
    PhishingCheckRequest,
    PhishingCheckResponse,
)
from app.services.password_service import assess_password
from app.services.phishing_service import assess_url

router = APIRouter(tags=["tools"])


@router.post("/tools/password-check", response_model=PasswordCheckResponse,
             dependencies=[Depends(require_scope("tools"))])
def password_check(payload: PasswordCheckRequest):
    return assess_password(payload.password)


@router.post("/tools/phishing-check", response_model=PhishingCheckResponse,
             dependencies=[Depends(require_scope("tools"))])
def phishing_check(payload: PhishingCheckRequest):
    return assess_url(payload.url)
