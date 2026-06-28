"""
Notification schemas — Pydantic v2.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    CONSOLE = "console"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    DATADOG = "datadog"
    EMAIL = "email"


class AlertPayload(BaseModel):
    """
    Mirrors monitoring_service Alert schema.
    Sent by monitoring_service to POST /notify/alert,
    or fetched from GET /monitor/alerts.
    """
    alert_type: str
    severity: AlertSeverity
    resource: str
    message: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    meta: dict[str, Any] = Field(default_factory=dict)


class NotificationRecord(BaseModel):
    """A dispatched notification stored in the in-memory log."""
    id: str
    alert: AlertPayload
    channels: list[NotificationChannel]
    dispatched_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool
    errors: list[str] = Field(default_factory=list)


class ChannelStatusResponse(BaseModel):
    """Returned by GET /notify/channels — shows which channels are configured."""
    console: bool = True
    slack: bool
    discord: bool
    webhook: bool
    datadog: bool
    email: bool


class NotificationHistoryResponse(BaseModel):
    total: int
    notifications: list[NotificationRecord]


class WebhookAlertRequest(BaseModel):
    """Body for POST /notify/alert — push an alert directly."""
    alert: AlertPayload
    channels: Optional[list[NotificationChannel]] = None   # None = all configured
