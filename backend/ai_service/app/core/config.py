"""
AI Service configuration.
All values are read from .env (with AI_ prefix) or environment variables.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AI_",
        extra="ignore",
    )

    # ── Service identity ────────────────────────────────────────────────
    SERVICE_NAME: str = "ai-service"
    PORT: int = 8002
    DEBUG: bool = False

    # ── LLM / Ollama ────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: float = 120.0

    # ── Agentic loop ────────────────────────────────────────────────────
    MAX_TOOL_ITERATIONS: int = 8      # safety cap on recursive tool calls
    AGENT_TEMPERATURE: float = 0.1

    # ── Downstream services ─────────────────────────────────────────────
    K8S_SERVICE_URL: str = "http://localhost:8001"
    AUTH_SERVICE_URL: str = "http://localhost:8080"

    # ── Auth / JWT (shared secret with auth_service) ────────────────────
    JWT_SECRET_KEY: str = "your_super_secret_key_here_change_this"
    JWT_ALGORITHM: str = "HS256"

    # ── Conversation history ─────────────────────────────────────────────
    MAX_HISTORY_MESSAGES: int = 20    # rolling window per conversation


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
