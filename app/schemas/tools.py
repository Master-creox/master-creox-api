from __future__ import annotations

from pydantic import BaseModel, Field


class PasswordCheckRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class PasswordCheckResponse(BaseModel):
    score: int
    label: str
    feedback: list[str]


class PhishingCheckRequest(BaseModel):
    url: str = Field(min_length=3, max_length=2048)


class PhishingCheckResponse(BaseModel):
    url: str
    risk_score: int
    is_suspicious: bool
    reasons: list[str]


class CreateKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    scopes: list[str] = Field(default_factory=lambda: ["tools"])
