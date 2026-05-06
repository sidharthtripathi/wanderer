from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="WANDERER_", extra="ignore")

    env: str = Field(default="dev")
    service_name: str = Field(default="core-api")
    log_level: str = Field(default="INFO")

    database_url: str = Field(
        default="postgresql+asyncpg://wanderer:wanderer@localhost:5432/wanderer"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    firebase_project_id: str = Field(default="")
    firebase_credentials_path: str = Field(default="")

    play_billing_package_name: str = Field(default="app.wanderer")

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
