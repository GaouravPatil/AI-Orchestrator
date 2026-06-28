"""
Notification Service configuration.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NOTIFY_",
        extra="ignore",
    )

    # ── Service identity ─────────────────────────────────────────────────
    SERVICE_NAME: str = "notification-service"
    PORT: int = 8004
    DEBUG: bool = False

    # ── Polling from monitoring service ──────────────────────────────────
    MONITORING_SERVICE_URL: str = "http://localhost:8003"
    POLL_INTERVAL_SECONDS: int = 60     # how often to check for new alerts
    AUTH_SERVICE_URL: str = "http://localhost:8080"

    # ── Auth ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "your_super_secret_key_here_change_this"
    JWT_ALGORITHM: str = "HS256"
    INTERNAL_JWT: str = ""              # token to call monitoring service

    # ── Alert deduplication ──────────────────────────────────────────────
    # Suppress re-notifying the same alert_type+resource for this many seconds
    DEDUP_WINDOW_SECONDS: int = 300     # 5 minutes

    # ── Channels ─────────────────────────────────────────────────────────
    # Slack
    SLACK_WEBHOOK_URL: str = ""         # e.g. https://hooks.slack.com/...
    SLACK_CHANNEL: str = "#k8s-alerts"

    # Discord
    DISCORD_WEBHOOK_URL: str = ""       # e.g. https://discord.com/api/webhooks/...

    # Generic webhook (POST JSON AlertPayload to any URL — custom receivers)
    GENERIC_WEBHOOK_URL: str = ""

    # Datadog Events API
    # Get your API key at: https://app.datadoghq.com/organization-settings/api-keys
    DATADOG_API_KEY: str = ""
    # Use "datadoghq.com" for US, "datadoghq.eu" for EU
    DATADOG_SITE: str = "datadoghq.com"
    # Comma-separated tags added to every Datadog event
    DATADOG_TAGS: str = "source:k8s-orchestrator,env:local"

    # Email (SMTP) — optional
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "alerts@orchestrator.local"
    SMTP_TO: str = ""                   # comma-separated recipients


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
