"""Model adapter registry (Phase 4 will plug real models behind these ids)."""
from fastapi import APIRouter, Depends

from app.core.security import require_scope

router = APIRouter(tags=["ai"])

MODELS = [
    {"id": "gemini", "type": "cloud", "status": "not_configured",
     "note": "Configure the provider key on the server to activate."},
]


@router.get("/models", dependencies=[Depends(require_scope("chat"))])
def list_models():
    return {"models": MODELS}
