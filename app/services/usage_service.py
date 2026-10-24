"""Usage tracking + statistics (Phase 3)."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.tables import APIKey, UsageLog, User


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UsageService:
    def __init__(self, session_factory=SessionLocal):
        self._session = session_factory

    def record(self, key_id, user_id, endpoint: str, method: str,
               status_code: int, latency_ms: float) -> None:
        try:
            with self._session() as s:
                s.add(UsageLog(key_id=key_id, user_id=user_id, endpoint=endpoint,
                               method=method, status_code=status_code,
                               latency_ms=round(latency_ms, 2), created_at=_now()))
                s.commit()
        except Exception:
            pass  # usage logging must never break a request

    def stats_for_user(self, user_id: int) -> dict:
        with self._session() as s:
            key_ids = s.scalars(select(APIKey.id).where(APIKey.user_id == user_id)).all()
            rows = s.scalars(
                select(UsageLog).where(
                    (UsageLog.user_id == user_id) | (UsageLog.key_id.in_(key_ids or [-1])))
            ).all()
        by_endpoint = Counter(r.endpoint for r in rows)
        by_day = Counter(r.created_at[:10] for r in rows)
        return {"total_requests": len(rows),
                "by_endpoint": dict(by_endpoint),
                "by_day": dict(sorted(by_day.items())),
                "keys": len(key_ids)}

    def platform_stats(self) -> dict:
        with self._session() as s:
            total_users = len(s.scalars(select(User.id)).all())
            total_keys = len(s.scalars(select(APIKey.id).where(APIKey.revoked == False)).all())  # noqa: E712
            rows = s.scalars(select(UsageLog)).all()
        by_endpoint = Counter(r.endpoint for r in rows)
        today = _now()[:10]
        return {"total_users": total_users,
                "active_keys": total_keys,
                "total_requests": len(rows),
                "requests_today": sum(1 for r in rows if r.created_at[:10] == today),
                "top_endpoints": dict(by_endpoint.most_common(5))}
