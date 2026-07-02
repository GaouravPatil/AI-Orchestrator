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

    # ── LLM Provider Setup ──────────────────────────────────────────────
    LLM_PROVIDER: str = "gemini"                                   # "gemini", "ollama", "openrouter", "openai"
    LLM_BASE_URL: str = ""                                         # e.g. "http://localhost:11434/v1" for Ollama
    LLM_API_KEY: str = ""                                          # optional for local setups

    # ── Google Gemini LLM defaults ─────────────────────────────────────
    GOOGLE_API_KEY: str = ""                                       # required if using gemini
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemini-2.0-flash"                         # default fallback model
    GEMINI_TIMEOUT: float = 60.0

    # ── OpenRouter defaults ─────────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ── Multi-Model Router / Bifurcation ──────────────────────────────
    MODEL_ROUTER: str = "gemini-2.0-flash"                         # routing and splitting (e.g. "google/gemini-2.5-flash", "openrouter/qwen/qwen-2.5-coder-32b:free")
    MODEL_FAST: str = "gemini-2.0-flash"                           # cheap/fast read-only queries and general chat
    MODEL_COMPLEX: str = "gemini-1.5-pro"                          # accurate/smart for admin changes (e.g. "openrouter/deepseek/deepseek-r1:free")

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
