"""Master CreoX API — application entry point."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import error_body, new_request_id, register_error_handlers
from app.core.rate_limit import RateLimiter
from app.services.audit_service import AuditService
from app.services.key_service import KeyService
from app.services.user_service import UserService


def create_app(rate_limit_per_minute: int | None = None) -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="One secure API platform for CreoX projects — Jarvis, BabyCoach and future apps.",
    )
    app.state.key_service = KeyService(settings.database_path)
    app.state.user_service = UserService(settings.database_path)
    app.state.audit_service = AuditService(settings.database_path)
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
