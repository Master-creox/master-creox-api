"""Conversation memory (Phase 4): sessions + messages.

A session belongs to one (key_id, user_id) pair. It is readable only by
that same key or by that same user — any other caller gets "not found",
never a hint that the session exists.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models.tables import Conversation, Message


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatService:
    def __init__(self, session_factory=SessionLocal):
        self._session = session_factory

    def create_session(self, key_id: int | None, user_id: int | None,
                       title: str | None = None) -> dict:
        with self._session() as s:
            row = Conversation(key_id=key_id, user_id=user_id,
                               title=title or "New chat", created_at=_now())
            s.add(row)
            s.commit()
            return {"id": row.id, "title": row.title, "created_at": row.created_at}

    def list_sessions(self, key_id: int | None, user_id: int | None) -> list[dict]:
        with self._session() as s:
            if user_id is not None:
                stmt = select(Conversation).where(
                    or_(Conversation.key_id == key_id, Conversation.user_id == user_id))
            else:
                stmt = select(Conversation).where(Conversation.key_id == key_id)
            rows = s.scalars(stmt.order_by(Conversation.id)).all()
            return [{"id": r.id, "title": r.title, "created_at": r.created_at} for r in rows]

    def _owned_session(self, s, session_id: int, key_id, user_id):
        row = s.get(Conversation, session_id)
        if row is None:
            return None
        if row.key_id == key_id:
            return row
        if row.user_id is not None and row.user_id == user_id:
            return row
        return None

    def get_session(self, session_id: int, key_id, user_id) -> dict | None:
        with self._session() as s:
            row = self._owned_session(s, session_id, key_id, user_id)
            if row is None:
                return None
            return {"id": row.id, "title": row.title, "created_at": row.created_at}

    def add_message(self, session_id: int, role: str, content: str) -> dict:
        with self._session() as s:
            row = Message(conversation_id=session_id, role=role,
                          content=content, created_at=_now())
            s.add(row)
            s.commit()
            return {"id": row.id, "role": role, "content": content,
                    "created_at": row.created_at}

    def list_messages(self, session_id: int, key_id, user_id) -> list[dict] | None:
        with self._session() as s:
            if self._owned_session(s, session_id, key_id, user_id) is None:
                return None
            rows = s.scalars(
                select(Message).where(Message.conversation_id == session_id)
                .order_by(Message.id)).all()
            return [{"id": r.id, "role": r.role, "content": r.content,
                     "created_at": r.created_at} for r in rows]
