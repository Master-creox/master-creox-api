"""Chat schemas (Phase 4)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=1, max_length=20000)


class ChatCompletionRequest(BaseModel):
    model: str = Field(min_length=1, max_length=120)
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float | None = None
    session_id: int | None = None


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
