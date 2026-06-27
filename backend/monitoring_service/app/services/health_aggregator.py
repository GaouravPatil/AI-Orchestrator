"""
HealthAggregator — derives ClusterHealthResponse from the latest snapshot + alerts.
"""
from typing import Optional

from monitoring_service.app.schemas.monitor import (
    Alert,
    AlertSeverity,
    AlertType,
    ClusterHealthResponse,
    ClusterSnapshot,
    DeploymentHealthSummary,
    NodeHealthSummary,
    PodHealthSummary,
)


class HealthAggregator:

    def summarise(
        self,
        snapshot: Optional[ClusterSnapshot],
        alerts: list[Alert],
    ) -> ClusterHealthResponse:

        if snapshot is None:
            return ClusterHealthResponse(
                status="unknown",
                score=0.0,
                last_updated=None,
                pods=PodHealthSummary(
                    total=0, running=0, pending=0, failed=0,
                    unknown=0, crash_looping=0, high_restart=0,
                ),
                nodes=NodeHealthSummary(total=0, ready=0, not_ready=0),
                deployments=DeploymentHealthSummary(
                    total=0, healthy=0, degraded=0, unavailable=0,
                ),
                active_alerts=alerts,
                total_alerts=len(alerts),
            )

        # ── Pod summary ───────────────────────────────────────────────────
        pod_counts = dict(running=0, pending=0, failed=0, unknown=0,
                          crash_looping=0, high_restart=0)
        for pod in snapshot.pods:
            status = (pod.status or "unknown").lower()
            if "crashloop" in status:
                pod_counts["crash_looping"] += 1
            elif status == "running":
                pod_counts["running"] += 1
            elif status == "pending":
                pod_counts["pending"] += 1
            elif status == "failed":
                pod_counts["failed"] += 1
            else:
                pod_counts["unknown"] += 1

            if pod.restarts >= 5:
                pod_counts["high_restart"] += 1

        pod_summary = PodHealthSummary(
            total=len(snapshot.pods),
            **pod_counts,
        )

        # ── Node summary ──────────────────────────────────────────────────
        ready_nodes = sum(1 for n in snapshot.nodes if n.status.lower() == "ready")
        node_summary = NodeHealthSummary(
            total=len(snapshot.nodes),
            ready=ready_nodes,
            not_ready=len(snapshot.nodes) - ready_nodes,
        )

        # ── Deployment summary ────────────────────────────────────────────
        dep_healthy = dep_degraded = dep_unavailable = 0
        for d in snapshot.deployments:
            desired = d.replicas or 0
            ready = d.ready_replicas or 0
            if ready == desired and desired > 0:
                dep_healthy += 1
            elif ready == 0:
                dep_unavailable += 1
            else:
                dep_degraded += 1

        dep_summary = DeploymentHealthSummary(
            total=len(snapshot.deployments),
            healthy=dep_healthy,
            degraded=dep_degraded,
            unavailable=dep_unavailable,
        )

        # ── Cluster score & status ────────────────────────────────────────
        score = self._compute_score(pod_summary, node_summary, dep_summary, alerts)
        if score >= 0.9:
            status = "healthy"
        elif score >= 0.6:
            status = "degraded"
        else:
            status = "critical"

        return ClusterHealthResponse(
            status=status,
            score=round(score, 3),
            last_updated=snapshot.timestamp,
            pods=pod_summary,
            nodes=node_summary,
            deployments=dep_summary,
            active_alerts=alerts,
            total_alerts=len(alerts),
        )

    # ── Score computation ─────────────────────────────────────────────────────

    def _compute_score(
        self,
        pods: PodHealthSummary,
        nodes: NodeHealthSummary,
        deps: DeploymentHealthSummary,
        alerts: list[Alert],
    ) -> float:
        score = 1.0

        # Deduct for critical alerts
        critical = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
        warning  = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)
        score -= critical * 0.15
        score -= warning  * 0.05

        # Deduct for pod health
        if pods.total > 0:
            bad_pods = pods.crash_looping + pods.failed + pods.pending
            score -= (bad_pods / pods.total) * 0.3

        # Deduct for node health
        if nodes.total > 0:
            score -= (nodes.not_ready / nodes.total) * 0.3

        # Deduct for deployment health
        if deps.total > 0:
            score -= (deps.unavailable / deps.total) * 0.2
            score -= (deps.degraded   / deps.total) * 0.1

        return max(0.0, min(1.0, score))


# ── Singleton ──────────────────────────────────────────────────────────────────
health_aggregator = HealthAggregator()
