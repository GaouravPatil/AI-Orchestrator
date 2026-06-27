"""
NotificationDispatcher — sends alerts to all configured channels.

Channels:
  console  — always active (structured log line)
  slack    — POST to Slack Incoming Webhook URL
  discord  — POST to Discord Webhook URL
  webhook  — POST JSON to any generic URL
  email    — SMTP (optional, requires smtplib config)

Design: each channel method is independent and never raises —
it returns (success: bool, error: str | None) so one failing
channel never blocks the others.
"""
import json
import smtplib
import uuid
from collections import deque
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional

import httpx

from notification_service.app.core.config import settings
from notification_service.app.core.logger import logger
from notification_service.app.schemas.notification import (
    AlertPayload,
    AlertSeverity,
    NotificationChannel,
    NotificationRecord,
)

# ── Severity emoji map ────────────────────────────────────────────────────────
SEVERITY_EMOJI = {
    AlertSeverity.CRITICAL: "🔴",
    AlertSeverity.WARNING:  "🟡",
    AlertSeverity.INFO:     "🔵",
}


class NotificationDispatcher:

    def __init__(self):
        # In-memory notification history (ring buffer)
        self._history: deque[NotificationRecord] = deque(maxlen=500)

        # Deduplication: key = (alert_type, resource), value = last-notified datetime
        self._dedup: dict[tuple, datetime] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def history(self) -> list[NotificationRecord]:
        return list(self._history)

    def dispatch(
        self,
        alert: AlertPayload,
        channels: Optional[list[NotificationChannel]] = None,
    ) -> NotificationRecord:
        """
        Send alert to all requested channels (or all configured ones).
        Deduplication is applied before dispatching.
        Returns a NotificationRecord regardless of channel results.
        """
        # ── Deduplication check ───────────────────────────────────────────
        dedup_key = (alert.alert_type, alert.resource)
        last_sent = self._dedup.get(dedup_key)
        window = timedelta(seconds=settings.DEDUP_WINDOW_SECONDS)

        if last_sent and (datetime.utcnow() - last_sent) < window:
            logger.debug(
                f"Suppressed duplicate alert: {alert.alert_type} / {alert.resource} "
                f"(last sent {last_sent.isoformat()})"
            )
            # Return a suppressed record (not stored in history)
            return NotificationRecord(
                id=str(uuid.uuid4()),
                alert=alert,
                channels=[],
                success=True,
                errors=["suppressed (dedup)"],
            )

        # ── Resolve channels ──────────────────────────────────────────────
        active = channels or self._active_channels()

        successes: list[NotificationChannel] = []
        errors: list[str] = []

        for ch in active:
            ok, err = self._dispatch_to(ch, alert)
            if ok:
                successes.append(ch)
            else:
                errors.append(f"{ch.value}: {err}")

        overall_ok = len(successes) > 0 or len(active) == 0

        # Update dedup map only on successful dispatch
        if overall_ok:
            self._dedup[dedup_key] = datetime.utcnow()

        record = NotificationRecord(
            id=str(uuid.uuid4()),
            alert=alert,
            channels=active,
            success=overall_ok,
            errors=errors,
        )
        self._history.append(record)
        return record

    def channel_status(self) -> dict:
        return {
            "console": True,
            "slack":   bool(settings.SLACK_WEBHOOK_URL),
            "discord": bool(settings.DISCORD_WEBHOOK_URL),
            "webhook": bool(settings.GENERIC_WEBHOOK_URL),
            "email":   bool(settings.SMTP_HOST and settings.SMTP_TO),
        }

    # ── Channel routing ───────────────────────────────────────────────────────

    def _active_channels(self) -> list[NotificationChannel]:
        active = [NotificationChannel.CONSOLE]
        if settings.SLACK_WEBHOOK_URL:
            active.append(NotificationChannel.SLACK)
        if settings.DISCORD_WEBHOOK_URL:
            active.append(NotificationChannel.DISCORD)
        if settings.GENERIC_WEBHOOK_URL:
            active.append(NotificationChannel.WEBHOOK)
        if settings.SMTP_HOST and settings.SMTP_TO:
            active.append(NotificationChannel.EMAIL)
        return active

    def _dispatch_to(
        self, channel: NotificationChannel, alert: AlertPayload
    ) -> tuple[bool, Optional[str]]:
        try:
            if channel == NotificationChannel.CONSOLE:
                return self._send_console(alert)
            elif channel == NotificationChannel.SLACK:
                return self._send_slack(alert)
            elif channel == NotificationChannel.DISCORD:
                return self._send_discord(alert)
            elif channel == NotificationChannel.WEBHOOK:
                return self._send_webhook(alert)
            elif channel == NotificationChannel.EMAIL:
                return self._send_email(alert)
        except Exception as e:
            return False, str(e)
        return False, "Unknown channel"

    # ── Channel implementations ───────────────────────────────────────────────

    def _send_console(self, alert: AlertPayload) -> tuple[bool, None]:
        emoji = SEVERITY_EMOJI.get(alert.severity, "⚪")
        logger.warning(
            f"{emoji} ALERT [{alert.severity.upper()}] "
            f"{alert.alert_type} | {alert.resource} | {alert.message}"
        )
        return True, None

    def _send_slack(self, alert: AlertPayload) -> tuple[bool, Optional[str]]:
        emoji = SEVERITY_EMOJI.get(alert.severity, "⚪")
        payload = {
            "text": f"{emoji} *[{alert.severity.upper()}]* `{alert.alert_type}`",
            "attachments": [{
                "color": {"critical": "danger", "warning": "warning", "info": "good"}.get(
                    alert.severity.value, "#aaa"
                ),
                "fields": [
                    {"title": "Resource", "value": alert.resource, "short": True},
                    {"title": "Message",  "value": alert.message,  "short": False},
                    {"title": "Time",     "value": alert.detected_at.isoformat(), "short": True},
                ],
            }],
        }
        r = httpx.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code != 200:
            return False, f"Slack HTTP {r.status_code}: {r.text}"
        return True, None

    def _send_discord(self, alert: AlertPayload) -> tuple[bool, Optional[str]]:
        emoji = SEVERITY_EMOJI.get(alert.severity, "⚪")
        color_map = {"critical": 0xFF0000, "warning": 0xFFAA00, "info": 0x3399FF}
        payload = {
            "embeds": [{
                "title": f"{emoji} {alert.alert_type} [{alert.severity.upper()}]",
                "description": alert.message,
                "color": color_map.get(alert.severity.value, 0xAAAAAA),
                "fields": [
                    {"name": "Resource", "value": alert.resource, "inline": True},
                    {"name": "Time", "value": alert.detected_at.isoformat(), "inline": True},
                ],
            }]
        }
        r = httpx.post(settings.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code not in (200, 204):
            return False, f"Discord HTTP {r.status_code}: {r.text}"
        return True, None

    def _send_webhook(self, alert: AlertPayload) -> tuple[bool, Optional[str]]:
        r = httpx.post(
            settings.GENERIC_WEBHOOK_URL,
            json=alert.model_dump(mode="json"),
            timeout=10,
        )
        if not r.is_success:
            return False, f"Webhook HTTP {r.status_code}: {r.text}"
        return True, None

    def _send_email(self, alert: AlertPayload) -> tuple[bool, Optional[str]]:
        emoji = SEVERITY_EMOJI.get(alert.severity, "")
        subject = f"{emoji} [{alert.severity.upper()}] {alert.alert_type} — {alert.resource}"
        body = (
            f"Alert Type : {alert.alert_type}\n"
            f"Severity   : {alert.severity.upper()}\n"
            f"Resource   : {alert.resource}\n"
            f"Message    : {alert.message}\n"
            f"Detected At: {alert.detected_at.isoformat()}\n"
        )
        if alert.meta:
            body += f"\nMeta:\n{json.dumps(alert.meta, indent=2)}"

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = settings.SMTP_TO

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USER:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(settings.SMTP_FROM, settings.SMTP_TO.split(","), msg.as_string())

        return True, None


# ── Singleton ──────────────────────────────────────────────────────────────────
dispatcher = NotificationDispatcher()
