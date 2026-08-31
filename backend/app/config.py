from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HippoEdge"
    environment: str = "development"
    database_url: str = "sqlite:///./hippoedge.db"
    provider: str = "demo"  # demo | turfbzh
    turfbzh_api_key: str | None = None
    turfbzh_base_url: str = "https://www.turf.bzh/api/v1"
    timezone: str = "Europe/Paris"
    refresh_seconds: int = 900
    auto_lock_minutes_before: int = 2
    methodology_version: str = "2026.08.31-v1"
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[2] / ".env"),
        env_prefix="HIPPOEDGE_",
        extra="ignore",
    )

    @property
    def cors_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
