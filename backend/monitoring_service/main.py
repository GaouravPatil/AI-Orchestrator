"""
Monitoring Service entry point.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from monitoring_service.app.api.monitor import monitor_router
from monitoring_service.app.core.config import settings
from monitoring_service.app.core.logger import logger
from monitoring_service.app.tasks.background import poll_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background polling on startup; cancel on shutdown."""
    logger.info(f"Starting {settings.SERVICE_NAME} on port {settings.PORT}")
    task = asyncio.create_task(poll_loop())
    logger.info("Background polling task started")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Background polling task stopped cleanly")


app = FastAPI(
    title="AI Orchestrator — Monitoring Service",
    description=(
        "Real-time cluster health monitoring, alerting, "
        "and Prometheus metrics for the AI DevOps Orchestrator."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.SERVICE_NAME,
        "port": settings.PORT,
        "docs": "/docs",
    }


app.include_router(monitor_router, prefix="/monitor", tags=["Monitoring"])
