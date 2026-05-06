"""Thin wrapper around the Google Gen AI SDK.

The actual conversation/tool logic lives in app.conversation.* (Slice 2);
this module just provides a configured client. We isolate it so tests can
replace the client without monkey-patching the SDK.
"""

from __future__ import annotations

from functools import lru_cache

from google import genai

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


@lru_cache
def get_client() -> genai.Client:
    settings = get_settings()
    if not settings.google_api_key:
        log.warning("gemini_client_missing_api_key")
    return genai.Client(api_key=settings.google_api_key or "MISSING")


def planner_model() -> str:
    return get_settings().gemini_planner_model


def narration_model() -> str:
    return get_settings().gemini_narration_model


def live_model() -> str:
    return get_settings().gemini_live_model


def embedding_model() -> str:
    return get_settings().gemini_embedding_model
