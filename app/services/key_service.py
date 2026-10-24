"""API key service (Phase 3: SQLAlchemy-backed).

Keys are shown ONCE at creation. Only their SHA-256 hash is stored.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.tables import APIKey

KEY_PREFIX = "mcx_"


def _hash(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KeyService:
    def __init__(self, session_factory=SessionLocal):
        self._session = session_factory

    def create_key(self, name: str, scopes: list[str], user_id: int | None = None) -> dict:
        raw = KEY_PREFIX + secrets.token_urlsafe(32)
        with self._session() as s:
            row = APIKey(name=name, key_hash=_hash(raw), scopes=",".join(scopes),
                         created_at=_now(), user_id=user_id)
            s.add(row)
            s.commit()
            kid = row.id
        return {"id": kid, "name": name, "key": raw, "scopes": scopes, "user_id": user_id,
                "note": "Store this key now — it is shown only once."}

    def list_keys(self, user_id: int | None = None, admin: bool = False) -> list[dict]:
        with self._session() as s:
            stmt = select(APIKey).order_by(APIKey.id)
            if not admin:
                stmt = stmt.where(APIKey.user_id == user_id)
            rows = s.scalars(stmt).all()
            return [{"id": r.id, "name": r.name, "scopes": r.scopes.split(","),
                     "created_at": r.created_at, "last_used_at": r.last_used_at,
                     "usage_count": r.usage_count, "revoked": bool(r.revoked),
                     "user_id": r.user_id} for r in rows]

    def revoke_key(self, key_id: int, user_id: int | None = None, admin: bool = False) -> bool:
        with self._session() as s:
            row = s.get(APIKey, key_id)
            if row is None or row.revoked:
                return False
            if not admin and row.user_id != user_id:
                return False
            row.revoked = True
            s.commit()
            return True

    def lookup(self, raw_key: str) -> dict | None:
        """Return the record for a valid, non-revoked key (no usage bump)."""
        with self._session() as s:
            row = s.scalars(select(APIKey).where(APIKey.key_hash == _hash(raw_key))).first()
            if row is None or row.revoked:
                return None
            return {"id": row.id, "name": row.name,
                    "scopes": row.scopes.split(","), "user_id": row.user_id,
                    "created_at": row.created_at, "usage_count": row.usage_count}

    def rotate_key(self, key_id: int, user_id: int | None = None,
                   caller_key_id: int | None = None) -> dict | None:
        """Revoke ``key_id`` and issue a replacement with the same name,
        scopes and owner. Returns the new-key dict (shown once) or None if
        the key is not found, already revoked, or not the caller's. A key
        may always rotate itself (caller_key_id == key_id) even when it
        has no owning user (e.g. an admin-created key)."""
        with self._session() as s:
            row = s.get(APIKey, key_id)
            if row is None or row.revoked:
                return None
            if row.id != caller_key_id and row.user_id != user_id:
                return None
            row.revoked = True
            s.commit()
            name, scopes = row.name, row.scopes.split(",")
            owner = row.user_id
        return self.create_key(name, scopes, user_id=owner)

    def id_for_key(self, raw_key: str) -> tuple[int | None, int | None]:
        with self._session() as s:
            row = s.scalars(select(APIKey).where(APIKey.key_hash == _hash(raw_key))).first()
            return (row.id, row.user_id) if row else (None, None)

    def verify(self, raw_key: str, required_scope: str) -> dict | None:
        with self._session() as s:
            row = s.scalars(select(APIKey).where(APIKey.key_hash == _hash(raw_key))).first()
            if row is None or row.revoked:
                return None
            if required_scope not in row.scopes.split(","):
                return None
            row.usage_count += 1
            row.last_used_at = _now()
            s.commit()
            return {"id": row.id, "name": row.name, "user_id": row.user_id}
