from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI DevOps Orchestrator"

    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "postgresql://postgres:redhat@localhost:5432/orchestrator"

    JWT_SECRET_KEY: str = "69a685a741b01767b7c374456fc60297972b12956617bb7cf567c2d04500a2ae"

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Shared static key for service-to-service / internal calls (X-API-Key header)
    INTERNAL_API_KEY: str = "orchestrator-internal-key-change-me"

    REDIS_URL: str = "redis://localhost:6379"

    AI_MODEL: str = "llama3"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()