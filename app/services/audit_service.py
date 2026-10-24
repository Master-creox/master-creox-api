"""Audit log (SQLAlchemy): who did what, when — auth and key events."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select

from app.db.session import SessionLocal
from app.models.tables import AuditLog


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditService:
    def __init__(self, session_factory=SessionLocal):
        self._session = session_factory

    def log(self, actor: str, action: str, details: str = "") -> None:
        with self._session() as s:
            s.add(AuditLog(actor=actor, action=action, details=details, created_at=_now()))
            s.commit()

    def list_recent(self, limit: int = 50) -> list[dict]:
        with self._session() as s:
            rows = s.scalars(select(AuditLog).order_by(desc(AuditLog.id)).limit(limit)).all()
            return [{"id": r.id, "actor": r.actor, "action": r.action,
                     "details": r.details, "created_at": r.created_at} for r in rows]
