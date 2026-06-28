"""
Notification REST API router.
"""
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from notification_service.app.core.dependencies import get_current_user
from notification_service.app.core.logger import logger
from notification_service.app.schemas.notification import (
    AlertPayload,
    ChannelStatusResponse,
    NotificationHistoryResponse,
    WebhookAlertRequest,
)
from notification_service.app.services.dispatcher import dispatcher

notify_router = APIRouter()


# ── Push a single alert directly (internal use / monitoring_service push) ─────

@notify_router.post(
    "/alert",
    summary="Push an alert to all configured notification channels",
)
def push_alert(
    body: WebhookAlertRequest,
    _: dict = Depends(get_current_user),
):
    """
    Dispatch an alert to configured channels (Slack, Discord, webhook, email,
    console). Deduplication is applied automatically.

    Set `channels` to a list to target specific channels, or omit to use all
    configured ones.
    """
    record = dispatcher.dispatch(body.alert, channels=body.channels)
    logger.info(f"Alert dispatched: id={record.id} success={record.success}")
    return {
        "id": record.id,
        "success": record.success,
        "channels_used": [c.value for c in record.channels],
        "errors": record.errors,
    }


# ── Channel status ─────────────────────────────────────────────────────────────

@notify_router.get(
    "/channels",
    response_model=ChannelStatusResponse,
    summary="List which notification channels are configured",
)
def get_channels(_: dict = Depends(get_current_user)):
    return dispatcher.channel_status()


# ── Notification history ───────────────────────────────────────────────────────

@notify_router.get(
    "/history",
    response_model=NotificationHistoryResponse,
    summary="Notification dispatch history (last 500)",
)
def get_history(_: dict = Depends(get_current_user)):
    history = dispatcher.history
    return NotificationHistoryResponse(total=len(history), notifications=history)


# ── Health (no auth — used by monitoring poller) ───────────────────────────────

@notify_router.get("/health", include_in_schema=True, summary="Service health check")
def health():
    status = dispatcher.channel_status()
    return {
        "status": "running",
        "channels": status,
        "history_count": len(dispatcher.history),
    }


# ── Prometheus metrics — PUBLIC (no auth, Prometheus scrapes this) ────────────

@notify_router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrics for notification dispatch (public — no auth)",
    include_in_schema=True,
    tags=["Metrics"],
)
def get_metrics():
    """
    Exposes notification dispatch statistics in Prometheus exposition format.
    Prometheus scrapes this endpoint — no authentication required.
    """
    history = dispatcher.history

    # Aggregate counters from history
    total_dispatched = len(history)
    total_success = sum(1 for r in history if r.success)
    total_errors = sum(1 for r in history if not r.success)
    total_suppressed = sum(1 for r in history if "suppressed (dedup)" in r.errors)

    # Per-channel counts
    channel_counts: dict[str, int] = {}
    for record in history:
        for ch in record.channels:
            channel_counts[ch.value] = channel_counts.get(ch.value, 0) + 1

    # Per-severity counts
    severity_counts: dict[str, int] = {}
    for record in history:
        sev = record.alert.severity.value
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    lines = [
        "# HELP notify_dispatched_total Total notification dispatch attempts",
        "# TYPE notify_dispatched_total counter",
        f"notify_dispatched_total {total_dispatched}",
        "",
        "# HELP notify_success_total Successful notification dispatches",
        "# TYPE notify_success_total counter",
        f"notify_success_total {total_success}",
        "",
        "# HELP notify_errors_total Failed notification dispatches",
        "# TYPE notify_errors_total counter",
        f"notify_errors_total {total_errors}",
        "",
        "# HELP notify_suppressed_total Deduplicated (suppressed) alerts",
        "# TYPE notify_suppressed_total counter",
        f"notify_suppressed_total {total_suppressed}",
        "",
        "# HELP notify_history_size Current notification history buffer size",
        "# TYPE notify_history_size gauge",
        f"notify_history_size {total_dispatched}",
    ]

    # Per-channel breakdown
    lines += [
        "",
        "# HELP notify_channel_dispatched_total Dispatches per notification channel",
        "# TYPE notify_channel_dispatched_total counter",
    ]
    for ch, count in channel_counts.items():
        lines.append(f'notify_channel_dispatched_total{{channel="{ch}"}} {count}')

    # Per-severity breakdown
    lines += [
        "",
        "# HELP notify_alert_severity_total Alerts dispatched per severity",
        "# TYPE notify_alert_severity_total counter",
    ]
    for sev, count in severity_counts.items():
        lines.append(f'notify_alert_severity_total{{severity="{sev}"}} {count}')

    return "\n".join(lines) + "\n"
