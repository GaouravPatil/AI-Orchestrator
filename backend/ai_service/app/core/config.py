"""
AI Service configuration.
All values are read from .env (with AI_ prefix) or environment variables.

LLM Provider: Google Gemini (OpenAI-compatible API — https://ai.google.dev/gemini-api/docs/openai)
Get your API key: https://aistudio.google.com/apikey
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

    # ── LLM / Google Gemini (via AI Studio) ────────────────────────────
    GOOGLE_API_KEY: str = ""                                       # required — set in .env
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"  # OpenAI-compat
    GEMINI_MODEL: str = "gemini-2.0-flash"                         # or gemini-1.5-pro, gemini-2.5-flash
    GEMINI_TIMEOUT: float = 60.0

    # ── Agentic loop ────────────────────────────────────────────────────
    MAX_TOOL_ITERATIONS: int = 8       # safety cap on recursive tool calls
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
