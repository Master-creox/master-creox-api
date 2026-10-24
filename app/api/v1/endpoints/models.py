"""Model registry (Phase 4: built-in CreoX engine, always active)."""
from fastapi import APIRouter, Depends

from app.core.security import require_scope

router = APIRouter(tags=["ai"])


@router.get("/models", dependencies=[Depends(require_scope("chat"))])
def list_models():
    return {"models": [
        {"id": "creox", "type": "local", "provider": "creox",
         "status": "active",
         "note": "Built-in CreoX engine — no key required."},
    ]}
