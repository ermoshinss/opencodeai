"""Точка входа FastAPI-приложения."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.health import router as health_router
from app.core.logging import setup_logging
from app.modules.authorization.router import router as authorization_router
from app.modules.climate.router import router as climate_router
from app.modules.identity.router import router as identity_router
from app.modules.registry.router import router as registry_router
from app.modules.tenancy.router import router as tenancy_router

setup_logging()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="opencodeai API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    for router in (
        health_router,
        identity_router,
        tenancy_router,
        registry_router,
        authorization_router,
        climate_router,
    ):
        app.include_router(router, prefix=settings.api_prefix)
    return app


app = create_app()
