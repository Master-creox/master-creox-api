"""Master CreoX API — application entry point."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import new_request_id, register_error_handlers
from app.services.key_service import KeyService


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="One secure API platform for CreoX projects — Jarvis, BabyCoach and future apps.",
    )
    app.state.key_service = KeyService(settings.database_path)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Phase 1 (development). Restrict to CreoX apps in production.
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _request_id(request: Request, call_next):
        request.state.request_id = new_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    register_error_handlers(app)
    app.include_router(api_router, prefix=f"/api/{settings.api_version}")

    @app.get("/")
    def root():
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "health": f"/api/{settings.api_version}/health",
        }

    return app


app = create_app()
