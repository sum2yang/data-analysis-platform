import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 — register all models with Base.metadata

__all__ = ["create_app"]

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(debug=settings.DEBUG)

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers
    register_error_handlers(app)

    # Routes
    app.include_router(api_router)

    @app.on_event("startup")
    async def startup():
        settings.ensure_dirs()
        Base.metadata.create_all(bind=engine)
        logger.info("Application started: %s v%s", settings.APP_NAME, settings.APP_VERSION)

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Application shutting down")

    return app


app = create_app()
