"""API key service.

Keys are shown ONCE at creation. Only their SHA-256 hash is stored
(same rule as the platform blueprint: key_hash, never the raw key).
SQLite is used for local/Phase-1; PostgreSQL arrives in Phase 3.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timezone

KEY_PREFIX = "mcx_"


def _hash(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KeyService:
    def __init__(self, database_path: str):
        self.database_path = database_path
        if database_path != ":memory:":
            os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS api_keys (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   key_hash TEXT NOT NULL UNIQUE,
                   scopes TEXT NOT NULL DEFAULT 'tools',
                   created_at TEXT NOT NULL,
                   last_used_at TEXT,
                   usage_count INTEGER NOT NULL DEFAULT 0,
                   revoked INTEGER NOT NULL DEFAULT 0
               )"""
        )
        self._conn.commit()

    def create_key(self, name: str, scopes: list[str]) -> dict:
        raw = KEY_PREFIX + secrets.token_urlsafe(32)
        cur = self._conn.execute(
            "INSERT INTO api_keys (name, key_hash, scopes, created_at) VALUES (?, ?, ?, ?)",
            (name, _hash(raw), ",".join(scopes), _now()),
        )
        self._conn.commit()
        return {"id": cur.lastrowid, "name": name, "key": raw, "scopes": scopes,
                "note": "Store this key now — it is shown only once."}

    def list_keys(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, name, scopes, created_at, last_used_at, usage_count, revoked FROM api_keys ORDER BY id"
        ).fetchall()
        return [dict(r) | {"scopes": r["scopes"].split(","), "revoked": bool(r["revoked"])} for r in rows]

    def revoke_key(self, key_id: int) -> bool:
        cur = self._conn.execute("UPDATE api_keys SET revoked = 1 WHERE id = ? AND revoked = 0", (key_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def verify(self, raw_key: str, required_scope: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM api_keys WHERE key_hash = ?", (_hash(raw_key),)
        ).fetchone()
        if row is None or row["revoked"]:
            return None
        if required_scope not in row["scopes"].split(","):
            return None
        self._conn.execute(
            "UPDATE api_keys SET usage_count = usage_count + 1, last_used_at = ? WHERE id = ?",
            (_now(), row["id"]),
        )
        self._conn.commit()
        return dict(row)
