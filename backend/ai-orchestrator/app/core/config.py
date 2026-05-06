from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="WANDERER_", extra="ignore")

    env: str = Field(default="dev")
    service_name: str = Field(default="ai-orchestrator")
    log_level: str = Field(default="INFO")

    database_url: str = Field(
        default="postgresql+asyncpg://wanderer:wanderer@localhost:5432/wanderer"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    qdrant_url: str = Field(default="http://localhost:6333")

    # Gemini
    google_api_key: str = Field(default="")
    gemini_planner_model: str = Field(default="gemini-2.5-pro")
    gemini_narration_model: str = Field(default="gemini-2.5-flash")
    gemini_live_model: str = Field(default="gemini-2.5-flash-live-preview")
    gemini_embedding_model: str = Field(default="gemini-embedding-001")

    # Tool budgets
    tool_default_timeout_ms: int = Field(default=1500)
    tool_route_timeout_ms: int = Field(default=3000)

    # Realtime edge (for narration callbacks etc.)
    realtime_edge_grpc_url: str = Field(default="realtime-edge:9090")

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    firebase_project_id: str = Field(default="")
    firebase_credentials_path: str = Field(default="")


@lru_cache
def get_settings() -> Settings:
    return Settings()
