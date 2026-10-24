"""Usage tracking + statistics (Phases 3–4)."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models.tables import APIKey, UsageLog, User


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UsageService:
    def __init__(self, session_factory=SessionLocal):
        self._session = session_factory

    def record(self, key_id, user_id, endpoint: str, method: str,
               status_code: int, latency_ms: float,
               model: str | None = None, tokens: int | None = None) -> None:
        try:
            with self._session() as s:
                s.add(UsageLog(key_id=key_id, user_id=user_id, endpoint=endpoint,
                               method=method, status_code=status_code,
                               latency_ms=round(latency_ms, 2), created_at=_now(),
                               model=model, tokens=tokens))
                s.commit()
        except Exception:
            pass  # usage logging must never break a request

    def _rows_for(self, s, user_id: int | None, key_id: int | None):
        """Rows belonging to a user (via user_id or their keys) and/or a key."""
        conditions = []
        if user_id is not None:
            key_ids = s.scalars(select(APIKey.id).where(APIKey.user_id == user_id)).all()
            conditions.append(UsageLog.user_id == user_id)
            if key_ids:
                conditions.append(UsageLog.key_id.in_(key_ids))
        if key_id is not None:
            conditions.append(UsageLog.key_id == key_id)
        if not conditions:
            return []
        return s.scalars(select(UsageLog).where(or_(*conditions))).all()

    def stats_for_user(self, user_id: int) -> dict:
        with self._session() as s:
            key_ids = s.scalars(select(APIKey.id).where(APIKey.user_id == user_id)).all()
            rows = s.scalars(
                select(UsageLog).where(
                    (UsageLog.user_id == user_id) | (UsageLog.key_id.in_(key_ids or [-1])))
            ).all()
        by_endpoint = Counter(r.endpoint for r in rows)
        by_day = Counter(r.created_at[:10] for r in rows)
        by_model = Counter(r.model for r in rows if r.model)
        return {"total_requests": len(rows),
                "by_endpoint": dict(by_endpoint),
                "by_day": dict(sorted(by_day.items())),
                "by_model": dict(by_model),
                "total_tokens": sum(r.tokens or 0 for r in rows),
                "keys": len(key_ids)}

    def breakdown(self, user_id: int | None = None, key_id: int | None = None) -> dict:
        """Per-endpoint / per-model / per-day usage, scoped to a user and/or key."""
        with self._session() as s:
            rows = self._rows_for(s, user_id, key_id)
        by_endpoint = Counter(r.endpoint for r in rows)
        by_model = Counter(r.model for r in rows if r.model)
        by_day = Counter(r.created_at[:10] for r in rows)
        return {"total_requests": len(rows),
                "total_tokens": sum(r.tokens or 0 for r in rows),
                "by_endpoint": dict(by_endpoint),
                "by_model": dict(by_model),
                "by_day": dict(sorted(by_day.items()))}

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
