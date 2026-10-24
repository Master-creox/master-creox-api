"""Application configuration — everything comes from environment variables.

Secrets are NEVER stored in code or in git. See .env.example.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.environ.get("APP_NAME", "Master CreoX API")
    version: str = "0.2.0"
    api_version: str = "v1"
    environment: str = os.environ.get("ENVIRONMENT", "development")
    database_path: str = os.environ.get("DATABASE_PATH", "data/master_creox.db")
    # Bootstrap admin key: required to create/revoke API keys via the API.
    # Set MASTER_CREOX_ADMIN_KEY in the environment (never commit it).
    admin_key: str | None = os.environ.get("MASTER_CREOX_ADMIN_KEY")
    # JWT (Phase 2). Set JWT_SECRET in production — the default is dev-only.
    jwt_secret: str = os.environ.get("JWT_SECRET", "dev-only-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))
    # Basic rate limiting (Phase 2): requests per minute per key/IP.
    rate_limit_per_minute: int = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "100"))


settings = Settings()
