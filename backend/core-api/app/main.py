"""Wanderer core API entrypoint.

Auth (Firebase token verification), community CRUD, subscription, points ledger.
Spec §4.4.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.v1 import router as v1_router
from app.core.config import get_settings
from app.core.errors import install_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    log = get_logger(__name__)

    app = FastAPI(
        title="Wanderer Core API",
        version="0.1.0",
        default_response_class=__import__("fastapi.responses", fromlist=["ORJSONResponse"]).ORJSONResponse,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_handlers(app)
    app.include_router(health.router)
    app.include_router(v1_router)

    log.info("core_api_started", env=settings.env)
    return app


app = create_app()
