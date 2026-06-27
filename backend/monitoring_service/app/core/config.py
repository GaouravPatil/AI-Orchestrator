"""
Monitoring Service configuration.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MONITOR_",
        extra="ignore",
    )

    # ── Service identity ─────────────────────────────────────────────────
    SERVICE_NAME: str = "monitoring-service"
    PORT: int = 8003
    DEBUG: bool = False

    # ── Polling ──────────────────────────────────────────────────────────
    POLL_INTERVAL_SECONDS: int = 30     # how often to scrape k8s_service
    SNAPSHOT_HISTORY: int = 60          # number of snapshots to keep (ring buffer)

    # ── Alert thresholds ─────────────────────────────────────────────────
    RESTART_ALERT_THRESHOLD: int = 5    # alert if pod restarts >= this
    READY_REPLICA_WARN_RATIO: float = 0.5  # alert if < 50% replicas ready

    # ── Downstream services ──────────────────────────────────────────────
    K8S_SERVICE_URL: str = "http://localhost:8001"
    AUTH_SERVICE_URL: str = "http://localhost:8080"

    # ── Auth ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "your_super_secret_key_here_change_this"
    JWT_ALGORITHM: str = "HS256"

    # ── Internal service token (used to call k8s_service) ───────────────
    # If set, the monitor uses this pre-issued admin token for polling.
    # Leave empty to poll unauthenticated (only works if k8s_service is open).
    INTERNAL_JWT: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
