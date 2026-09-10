from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from `HOURTIME_*` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="HOURTIME_",
        # The app is started from `backend/`, the shared .env lives at the repo root.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://hourtime:hourtime@localhost:5432/hourtime"
    sql_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"
    cache_backend: Literal["redis", "memory"] = "redis"
    session_cache_ttl_seconds: int = 300

    # Leave off once your own account exists: the instance faces the open internet.
    allow_registration: bool = True
    password_min_length: int = 10

    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 30
    session_retention_days: int = 90
    session_purge_interval_hours: int = 24

    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
