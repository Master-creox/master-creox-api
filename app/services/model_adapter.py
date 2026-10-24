"""Model adapter protocol (Phase 4).

Adapters implement this protocol so the chat endpoint never depends on one
engine. CreoXEngine is the first adapter — built into the API, offline and
key-free. A local LLM can be plugged in later behind the same protocol
without changing the endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ChatResult:
    reply: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@runtime_checkable
class ModelAdapter(Protocol):
    def complete(self, messages: list, model: str) -> ChatResult:
        """Return the assistant reply for a conversation.

        ``messages`` is a list of dicts (or objects) with ``role`` and
        ``content`` keys/attributes. ``model`` is the engine id the caller
        asked for (currently only ``creox`` is supported).
        """
        ...
