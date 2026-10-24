"""Master CreoX API — application entry point."""
from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import error_body, new_request_id, register_error_handlers
from app.core.rate_limit import RateLimiter
from app.db.session import init_db
from app.services.audit_service import AuditService
from app.services.key_service import KeyService
from app.services.usage_service import UsageService
from app.services.user_service import UserService


def create_app(rate_limit_per_minute: int | None = None) -> FastAPI:
    init_db()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="One secure API platform for CreoX projects — Jarvis, BabyCoach and future apps.",
    )
    app.state.key_service = KeyService()
    app.state.user_service = UserService()
    app.state.audit_service = AuditService()
    app.state.usage_service = UsageService()
    app.state.rate_limiter = RateLimiter(
        rate_limit_per_minute if rate_limit_per_minute is not None else settings.rate_limit_per_minute)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Development. Restrict to CreoX apps in production.
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _request_id(request: Request, call_next):
        request.state.request_id = new_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.middleware("http")
    async def _rate_limit(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and not path.endswith("/health"):
            identity = request.headers.get("x-api-key") or (request.client.host if request.client else "unknown")
            if not app.state.rate_limiter.allow(identity):
                rid = getattr(request.state, "request_id", new_request_id())
                return JSONResponse(
                    status_code=429,
                    content=error_body("rate_limited", "Too many requests — slow down.", rid),
                    headers={"Retry-After": "60"},
                )
        return await call_next(request)

    @app.middleware("http")
    async def _usage_tracking(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/api/") and not path.endswith("/health"):
            key_id = user_id = None
            raw_key = request.headers.get("x-api-key")
            if raw_key:
                key_id, user_id = app.state.key_service.id_for_key(raw_key)
            if user_id is None:
                auth = request.headers.get("authorization", "")
                if auth.lower().startswith("bearer "):
                    try:
                        from app.services.token_service import decode_access_token
                        user_id = int(decode_access_token(auth.split(" ", 1)[1].strip())["sub"])
                    except Exception:
                        user_id = None
            app.state.usage_service.record(
                key_id, user_id, path, request.method,
                response.status_code, (time.perf_counter() - start) * 1000,
                model=getattr(request.state, "chat_model", None),
                tokens=getattr(request.state, "chat_tokens", None))
        return response

    register_error_handlers(app)
    app.include_router(api_router, prefix=f"/api/{settings.api_version}")

    @app.get("/")
    def root():
        return {
            "service": settings.app_name,
            "version": settings.version,
            "docs": "/docs",
            "health": f"/api/{settings.api_version}/health",
        }

    return app


app = create_app()
