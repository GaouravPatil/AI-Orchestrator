"""
Monitoring REST API router.
All endpoints require JWT auth (via get_current_user dependency).
"""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from monitoring_service.app.core.dependencies import get_current_user
from monitoring_service.app.core.logger import logger
from monitoring_service.app.schemas.monitor import (
    AlertsResponse,
    ClusterHealthResponse,
    MetricsSnapshot,
)
from monitoring_service.app.services.alerting import alerting_engine
from monitoring_service.app.services.collector import collector
from monitoring_service.app.services.health_aggregator import health_aggregator

monitor_router = APIRouter(dependencies=[Depends(get_current_user)])

# Public router — no auth (Prometheus scrapes /metrics without credentials)
monitor_public_router = APIRouter()


# ── Cluster health overview ───────────────────────────────────────────────────

@monitor_router.get(
    "/cluster",
    response_model=ClusterHealthResponse,
    summary="Overall cluster health score and summary",
)
def get_cluster_health():
    """
    Returns a cluster health score (0.0 – 1.0), pod/node/deployment summaries,
    and all active alerts derived from the latest snapshot.
    """
    snapshot = collector.latest
    alerts = alerting_engine.evaluate(snapshot)
    return health_aggregator.summarise(snapshot, alerts)


# ── Active alerts ─────────────────────────────────────────────────────────────

@monitor_router.get(
    "/alerts",
    response_model=AlertsResponse,
    summary="List all active alerts",
)
def get_alerts():
    snapshot = collector.latest
    alerts = alerting_engine.evaluate(snapshot)
    return AlertsResponse(total=len(alerts), alerts=alerts)


# ── Pods ──────────────────────────────────────────────────────────────────────

@monitor_router.get("/pods", summary="Latest pod snapshot")
def get_pods():
    snapshot = collector.latest
    if snapshot is None:
        return {"pods": [], "message": "No snapshot collected yet"}
    return {
        "total": len(snapshot.pods),
        "last_updated": snapshot.timestamp,
        "pods": [p.model_dump() for p in snapshot.pods],
    }


# ── Nodes ─────────────────────────────────────────────────────────────────────

@monitor_router.get("/nodes", summary="Latest node snapshot")
def get_nodes():
    snapshot = collector.latest
    if snapshot is None:
        return {"nodes": [], "message": "No snapshot collected yet"}
    return {
        "total": len(snapshot.nodes),
        "last_updated": snapshot.timestamp,
        "nodes": [n.model_dump() for n in snapshot.nodes],
    }


# ── Deployments ───────────────────────────────────────────────────────────────

@monitor_router.get("/deployments", summary="Latest deployment snapshot")
def get_deployments():
    snapshot = collector.latest
    if snapshot is None:
        return {"deployments": [], "message": "No snapshot collected yet"}
    return {
        "total": len(snapshot.deployments),
        "last_updated": snapshot.timestamp,
        "deployments": [d.model_dump() for d in snapshot.deployments],
    }


# ── Snapshot history ──────────────────────────────────────────────────────────

@monitor_router.get(
    "/snapshots/latest",
    response_model=MetricsSnapshot,
    summary="Latest raw cluster snapshot",
)
def get_latest_snapshot():
    return MetricsSnapshot(
        snapshot=collector.latest,
        history_count=collector.history_count,
    )


@monitor_router.get("/snapshots/history", summary="All stored snapshots (timestamps only)")
def get_snapshot_history():
    history = collector.history
    return {
        "count": len(history),
        "snapshots": [
            {
                "timestamp": s.timestamp,
                "pods": len(s.pods),
                "nodes": len(s.nodes),
                "deployments": len(s.deployments),
                "error": s.scrape_error,
            }
            for s in history
        ],
    }


# ── Prometheus metrics — PUBLIC (no auth, Prometheus scraper) ────────────────

@monitor_public_router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus-compatible metrics (public — no auth required)",
    include_in_schema=True,
    tags=["Metrics"],
)
def get_prometheus_metrics():
    """
    Exposes key cluster metrics in Prometheus exposition format.
    Prometheus can scrape this endpoint directly.
    """
    snapshot = collector.latest
    alerts = alerting_engine.evaluate(snapshot)

    if snapshot is None:
        return "# No snapshot available yet\n"

    lines = [
        "# HELP k8s_pods_total Total number of pods",
        "# TYPE k8s_pods_total gauge",
        f"k8s_pods_total {len(snapshot.pods)}",
        "",
        "# HELP k8s_pods_running Running pods",
        "# TYPE k8s_pods_running gauge",
        f"k8s_pods_running {sum(1 for p in snapshot.pods if (p.status or '').lower() == 'running')}",
        "",
        "# HELP k8s_pods_pending Pending pods",
        "# TYPE k8s_pods_pending gauge",
        f"k8s_pods_pending {sum(1 for p in snapshot.pods if (p.status or '').lower() == 'pending')}",
        "",
        "# HELP k8s_pods_failed Failed pods",
        "# TYPE k8s_pods_failed gauge",
        f"k8s_pods_failed {sum(1 for p in snapshot.pods if (p.status or '').lower() == 'failed')}",
        "",
        "# HELP k8s_nodes_total Total cluster nodes",
        "# TYPE k8s_nodes_total gauge",
        f"k8s_nodes_total {len(snapshot.nodes)}",
        "",
        "# HELP k8s_nodes_ready Ready nodes",
        "# TYPE k8s_nodes_ready gauge",
        f"k8s_nodes_ready {sum(1 for n in snapshot.nodes if n.status.lower() == 'ready')}",
        "",
        "# HELP k8s_deployments_total Total deployments",
        "# TYPE k8s_deployments_total gauge",
        f"k8s_deployments_total {len(snapshot.deployments)}",
        "",
        "# HELP k8s_active_alerts Active alert count",
        "# TYPE k8s_active_alerts gauge",
        f"k8s_active_alerts {len(alerts)}",
        "",
        "# HELP k8s_critical_alerts Critical alert count",
        "# TYPE k8s_critical_alerts gauge",
        f"k8s_critical_alerts {sum(1 for a in alerts if a.severity.value == 'critical')}",
    ]

    # Per-pod restart counts
    lines += [
        "",
        "# HELP k8s_pod_restarts_total Restart count per pod",
        "# TYPE k8s_pod_restarts_total gauge",
    ]
    for pod in snapshot.pods:
        safe_name = pod.name.replace("-", "_").replace(".", "_")
        lines.append(
            f'k8s_pod_restarts_total{{namespace="{pod.namespace}",pod="{pod.name}"}} {pod.restarts}'
        )

    return "\n".join(lines) + "\n"
