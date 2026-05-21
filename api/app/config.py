from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    exa_api_key: str | None = Field(default=None, alias="EXA_API_KEY")
    database_url: str = Field(alias="DATABASE_URL")
    app_base_url: str = Field(default="http://localhost:3000", alias="APP_BASE_URL")
    cron_secret: str | None = Field(default=None, alias="CRON_SECRET")
    allowed_origins: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")
    scan_query_version: str = Field(default="v1", alias="SCAN_QUERY_VERSION")
    debug_raw_sources: bool = Field(default=False, alias="DEBUG_RAW_SOURCES")

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def exa_configured(self) -> bool:
        return bool(self.exa_api_key)

@lru_cache
def get_settings() -> Settings:
    return Settings()
