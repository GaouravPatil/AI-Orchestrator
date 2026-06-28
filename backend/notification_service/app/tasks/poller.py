"""
Background poller — periodically fetches active alerts from monitoring_service
and dispatches notifications for any new or re-fired ones.
"""
import asyncio

import httpx

from notification_service.app.core.config import settings
from notification_service.app.core.logger import logger
from notification_service.app.schemas.notification import AlertPayload, AlertSeverity
from notification_service.app.services.dispatcher import dispatcher


async def _fetch_alerts() -> list[dict]:
    """Call monitoring_service GET /monitor/alerts and return raw alert dicts."""
    url = f"{settings.MONITORING_SERVICE_URL}/monitor/alerts"
    headers = {}

    # Use shared internal API key (same as k8s/monitoring services use)
    from shared.core.config import settings as shared_settings
    headers["X-API-Key"] = shared_settings.INTERNAL_API_KEY

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("alerts", [])
    except Exception as exc:
        logger.warning(f"Poller: failed to fetch alerts from monitoring_service — {exc}")
        return []


async def alert_poller():
    """
    Runs forever as an asyncio task.
    Every POLL_INTERVAL_SECONDS it fetches active alerts and dispatches
    notifications (deduplication is handled inside the dispatcher).
    """
    logger.info(
        f"Alert poller started — polling every {settings.POLL_INTERVAL_SECONDS}s "
        f"from {settings.MONITORING_SERVICE_URL}"
    )

    while True:
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
        logger.debug("Poller: checking for alerts...")

        raw_alerts = await _fetch_alerts()
        if not raw_alerts:
            logger.debug("Poller: no active alerts.")
            continue

        logger.info(f"Poller: {len(raw_alerts)} alert(s) received from monitoring_service")

        for raw in raw_alerts:
            try:
                alert = AlertPayload(
                    alert_type=raw.get("alert_type", "unknown"),
                    severity=AlertSeverity(raw.get("severity", "info")),
                    resource=raw.get("resource", "unknown"),
                    message=raw.get("message", ""),
                    meta=raw.get("meta", {}),
                )
                dispatcher.dispatch(alert)
            except Exception as exc:
                logger.warning(f"Poller: failed to dispatch alert {raw} — {exc}")
