import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from notification_service.app.api.notify import notify_router
from notification_service.app.core.config import settings
from notification_service.app.core.logger import logger
from notification_service.app.tasks.poller import alert_poller

app = FastAPI(
    title="Notification Service",
    description=(
        "Dispatches cluster alerts to Slack, Discord, webhook, email, and console. "
        "Polls monitoring_service for active alerts and sends notifications with deduplication."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notify_router, prefix="/notify", tags=["Notifications"])


# ── Lifecycle ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info(f"Notification Service starting on port {settings.PORT}")
    # Launch the background alert poller as a fire-and-forget asyncio task
    asyncio.create_task(alert_poller())
    logger.info("Alert poller task scheduled.")


# ── Root ───────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "notification-service",
        "port": settings.PORT,
        "docs": "/docs",
    }
