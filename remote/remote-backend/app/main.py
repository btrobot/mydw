from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.self_service import router as self_service_router
from app.core.config import get_settings
from app.core.observability import RequestContextMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Remote Auth API",
        version="0.1.0",
        description="Phase 1 remote auth core bootstrap service.",
    )
    allowed_origins = [origin.strip() for origin in settings.CORS_ALLOW_ORIGINS.split(',') if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(auth_router)
    app.include_router(self_service_router)
    app.include_router(admin_router)

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        bearer_auth = schema.get("components", {}).get("securitySchemes", {}).get("BearerAuth")
        if isinstance(bearer_auth, dict):
            bearer_auth.setdefault("bearerFormat", "JWT")
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
