"""User accounts: registration + login with Argon2 hashing (SQLAlchemy)."""
from __future__ import annotations

from datetime import datetime, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select

from app.core.errors import APIError
from app.db.session import SessionLocal
from app.models.tables import User

_ph = PasswordHasher()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserService:
    def __init__(self, session_factory=SessionLocal):
        self._session = session_factory

    @staticmethod
    def _public(u: User) -> dict:
        return {"id": u.id, "name": u.name, "email": u.email,
                "role": u.role, "created_at": u.created_at}

    def register(self, name: str, email: str, password: str) -> dict:
        email = email.strip().lower()
        with self._session() as s:
            if s.scalars(select(User).where(User.email == email)).first():
                raise APIError(409, "email_already_registered",
                               "An account with this email already exists.")
            user = User(name=name.strip(), email=email,
                        password_hash=_ph.hash(password), role="user", created_at=_now())
            s.add(user)
            s.commit()
            return self._public(user)

    def authenticate(self, email: str, password: str) -> dict | None:
        with self._session() as s:
            user = s.scalars(select(User).where(User.email == email.strip().lower())).first()
            if user is None:
                return None
            try:
                _ph.verify(user.password_hash, password)
            except VerifyMismatchError:
                return None
            return self._public(user)

    def get_by_id(self, user_id: int) -> dict | None:
        with self._session() as s:
            user = s.get(User, user_id)
            return self._public(user) if user else None

    def list_users(self) -> list[dict]:
        with self._session() as s:
            return [self._public(u) for u in s.scalars(select(User).order_by(User.id)).all()]

    def count_users(self) -> int:
        with self._session() as s:
            return len(s.scalars(select(User.id)).all())
