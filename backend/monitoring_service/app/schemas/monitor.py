"""
Pydantic schemas for monitoring service.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    CRASH_LOOP = "CrashLoopBackOff"
    HIGH_RESTARTS = "HighRestartCount"
    NODE_NOT_READY = "NodeNotReady"
    DEPLOYMENT_DEGRADED = "DeploymentDegraded"
    POD_PENDING = "PodPending"
    POD_FAILED = "PodFailed"
    K8S_SERVICE_UNREACHABLE = "K8sServiceUnreachable"


# ── Snapshot models ───────────────────────────────────────────────────────────

class PodSnapshot(BaseModel):
    namespace: str
    name: str
    status: Optional[str] = None
    node: Optional[str] = None
    pod_ip: Optional[str] = None
    restarts: int = 0


class NodeSnapshot(BaseModel):
    name: str
    status: str
    roles: list[str] = Field(default_factory=list)
    cpu: Optional[str] = None
    memory: Optional[str] = None


class DeploymentSnapshot(BaseModel):
    namespace: str
    name: str
    replicas: Optional[int] = None
    ready_replicas: Optional[int] = None


class ClusterSnapshot(BaseModel):
    """Point-in-time view of the cluster, collected by the background poller."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pods: list[PodSnapshot] = Field(default_factory=list)
    nodes: list[NodeSnapshot] = Field(default_factory=list)
    deployments: list[DeploymentSnapshot] = Field(default_factory=list)
    scrape_error: Optional[str] = None   # set if k8s_service was unreachable


# ── Alert models ──────────────────────────────────────────────────────────────

class Alert(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    resource: str                       # e.g. "namespace/pod-name"
    message: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    meta: dict[str, Any] = Field(default_factory=dict)


# ── Summary / response models ─────────────────────────────────────────────────

class PodHealthSummary(BaseModel):
    total: int
    running: int
    pending: int
    failed: int
    unknown: int
    crash_looping: int
    high_restart: int


class NodeHealthSummary(BaseModel):
    total: int
    ready: int
    not_ready: int


class DeploymentHealthSummary(BaseModel):
    total: int
    healthy: int          # ready_replicas == replicas
    degraded: int         # ready_replicas < replicas
    unavailable: int      # ready_replicas == 0 or None


class ClusterHealthResponse(BaseModel):
    """Returned by GET /monitor/cluster"""
    status: str                          # "healthy" | "degraded" | "critical"
    score: float                         # 0.0 – 1.0
    last_updated: Optional[datetime]
    pods: PodHealthSummary
    nodes: NodeHealthSummary
    deployments: DeploymentHealthSummary
    active_alerts: list[Alert] = Field(default_factory=list)
    total_alerts: int = 0


class AlertsResponse(BaseModel):
    """Returned by GET /monitor/alerts"""
    total: int
    alerts: list[Alert]


class MetricsSnapshot(BaseModel):
    """Returned by GET /monitor/snapshots/latest"""
    snapshot: Optional[ClusterSnapshot]
    history_count: int
