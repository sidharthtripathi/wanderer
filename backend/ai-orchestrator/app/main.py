"""Wanderer AI Orchestrator entrypoint.

Owns conversation state, tool calls, memory, persona, and narration trigger logic.
Spec §4.2.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api import router as api_router
from app.core.config import get_settings
from app.core.errors import install_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    log = get_logger(__name__)

    app = FastAPI(
        title="Wanderer AI Orchestrator",
        version="0.1.0",
        default_response_class=ORJSONResponse,
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
    app.include_router(api_router)

    log.info("ai_orchestrator_started", env=settings.env)
    return app


app = create_app()
