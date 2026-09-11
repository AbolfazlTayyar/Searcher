from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables (or a `.env` file)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ES_HOST: str = "http://localhost:9200"
    ES_INDEX_NAME: str = "linkedin_profiles"
    CORS_ORIGINS: list[str] = ["http://localhost:4173"]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance, suitable for use as a FastAPI dependency."""
    return Settings()
