"""Audit log (Phase 2): who did what, when — auth and key events."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditService:
    def __init__(self, database_path: str):
        self.database_path = database_path
        if database_path != ":memory:":
            os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS audit_logs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   actor TEXT NOT NULL,
                   action TEXT NOT NULL,
                   details TEXT,
                   created_at TEXT NOT NULL
               )"""
        )
        self._conn.commit()

    def log(self, actor: str, action: str, details: str = "") -> None:
        self._conn.execute(
            "INSERT INTO audit_logs (actor, action, details, created_at) VALUES (?, ?, ?, ?)",
            (actor, action, details, _now()),
        )
        self._conn.commit()

    def list_recent(self, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, actor, action, details, created_at FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
