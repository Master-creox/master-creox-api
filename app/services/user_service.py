"""User accounts (Phase 2): registration + login with Argon2 password hashing."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.errors import APIError

_ph = PasswordHasher()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserService:
    def __init__(self, database_path: str):
        self.database_path = database_path
        if database_path != ":memory:":
            os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   email TEXT NOT NULL UNIQUE,
                   password_hash TEXT NOT NULL,
                   role TEXT NOT NULL DEFAULT 'user',
                   created_at TEXT NOT NULL
               )"""
        )
        self._conn.commit()

    @staticmethod
    def _public(row: sqlite3.Row) -> dict:
        return {"id": row["id"], "name": row["name"], "email": row["email"],
                "role": row["role"], "created_at": row["created_at"]}

    def register(self, name: str, email: str, password: str) -> dict:
        email = email.strip().lower()
        existing = self._conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise APIError(409, "email_already_registered", "An account with this email already exists.")
        cur = self._conn.execute(
            "INSERT INTO users (name, email, password_hash, role, created_at) VALUES (?, ?, ?, 'user', ?)",
            (name.strip(), email, _ph.hash(password), _now()),
        )
        self._conn.commit()
        return self.get_by_id(cur.lastrowid)

    def authenticate(self, email: str, password: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        if row is None:
            return None
        try:
            _ph.verify(row["password_hash"], password)
        except VerifyMismatchError:
            return None
        return self._public(row)

    def get_by_id(self, user_id: int) -> dict | None:
        row = self._conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._public(row) if row else None
