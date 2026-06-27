"""
Background polling task.
Uses asyncio + a simple loop (no extra scheduler dependency).
"""
import asyncio

from monitoring_service.app.core.config import settings
from monitoring_service.app.core.logger import logger
from monitoring_service.app.services.collector import collector


async def poll_loop():
    """
    Runs forever, calling collector.collect() every POLL_INTERVAL_SECONDS.
    Designed to be started as an asyncio background task in FastAPI's lifespan.
    """
    logger.info(
        f"Polling loop started — interval={settings.POLL_INTERVAL_SECONDS}s, "
        f"history={settings.SNAPSHOT_HISTORY} snapshots"
    )

    while True:
        try:
            collector.collect()
        except Exception as exc:
            logger.error(f"Unexpected error in poll_loop: {exc}", exc_info=True)

        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
