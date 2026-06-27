"""
AlertingEngine — analyses the latest ClusterSnapshot and produces Alerts.

Rules:
  • CrashLoopBackOff     — pod status contains "CrashLoop"
  • HighRestartCount     — pod restarts >= RESTART_ALERT_THRESHOLD
  • NodeNotReady         — node status != "Ready"
  • DeploymentDegraded   — ready_replicas / replicas < READY_REPLICA_WARN_RATIO
  • PodPending           — pod stuck in Pending
  • PodFailed            — pod in Failed state
  • K8sServiceUnreachable — snapshot has scrape_error set
"""
from datetime import datetime
from typing import Optional

from monitoring_service.app.core.config import settings
from monitoring_service.app.core.logger import logger
from monitoring_service.app.schemas.monitor import (
    Alert,
    AlertSeverity,
    AlertType,
    ClusterSnapshot,
)


class AlertingEngine:

    def evaluate(self, snapshot: Optional[ClusterSnapshot]) -> list[Alert]:
        """
        Run all alert rules against the given snapshot.
        Returns a (possibly empty) list of Alert objects.
        """
        if snapshot is None:
            return []

        alerts: list[Alert] = []

        # ── Service unreachable ────────────────────────────────────────────
        if snapshot.scrape_error:
            alerts.append(Alert(
                alert_type=AlertType.K8S_SERVICE_UNREACHABLE,
                severity=AlertSeverity.CRITICAL,
                resource="k8s_service",
                message=f"k8s_service scrape failed: {snapshot.scrape_error}",
                detected_at=snapshot.timestamp,
            ))
            return alerts   # no point checking further if data is stale

        # ── Pod rules ─────────────────────────────────────────────────────
        for pod in snapshot.pods:
            resource = f"{pod.namespace}/{pod.name}"
            status = (pod.status or "").lower()

            if "crashloop" in status:
                alerts.append(Alert(
                    alert_type=AlertType.CRASH_LOOP,
                    severity=AlertSeverity.CRITICAL,
                    resource=resource,
                    message=f"Pod '{pod.name}' is in CrashLoopBackOff",
                    detected_at=snapshot.timestamp,
                    meta={"restarts": pod.restarts, "node": pod.node},
                ))

            elif pod.restarts >= settings.RESTART_ALERT_THRESHOLD:
                alerts.append(Alert(
                    alert_type=AlertType.HIGH_RESTARTS,
                    severity=AlertSeverity.WARNING,
                    resource=resource,
                    message=(
                        f"Pod '{pod.name}' has restarted {pod.restarts} times "
                        f"(threshold: {settings.RESTART_ALERT_THRESHOLD})"
                    ),
                    detected_at=snapshot.timestamp,
                    meta={"restarts": pod.restarts},
                ))

            if status == "pending":
                alerts.append(Alert(
                    alert_type=AlertType.POD_PENDING,
                    severity=AlertSeverity.WARNING,
                    resource=resource,
                    message=f"Pod '{pod.name}' is stuck in Pending state",
                    detected_at=snapshot.timestamp,
                ))

            elif status == "failed":
                alerts.append(Alert(
                    alert_type=AlertType.POD_FAILED,
                    severity=AlertSeverity.CRITICAL,
                    resource=resource,
                    message=f"Pod '{pod.name}' is in Failed state",
                    detected_at=snapshot.timestamp,
                ))

        # ── Node rules ────────────────────────────────────────────────────
        for node in snapshot.nodes:
            if node.status.lower() != "ready":
                alerts.append(Alert(
                    alert_type=AlertType.NODE_NOT_READY,
                    severity=AlertSeverity.CRITICAL,
                    resource=node.name,
                    message=f"Node '{node.name}' is {node.status} (expected Ready)",
                    detected_at=snapshot.timestamp,
                    meta={"roles": node.roles},
                ))

        # ── Deployment rules ──────────────────────────────────────────────
        for dep in snapshot.deployments:
            resource = f"{dep.namespace}/{dep.name}"
            desired = dep.replicas or 0
            ready = dep.ready_replicas or 0

            if desired == 0:
                continue

            ratio = ready / desired
            if ratio < settings.READY_REPLICA_WARN_RATIO:
                severity = (
                    AlertSeverity.CRITICAL if ready == 0
                    else AlertSeverity.WARNING
                )
                alerts.append(Alert(
                    alert_type=AlertType.DEPLOYMENT_DEGRADED,
                    severity=severity,
                    resource=resource,
                    message=(
                        f"Deployment '{dep.name}' is degraded: "
                        f"{ready}/{desired} replicas ready"
                    ),
                    detected_at=snapshot.timestamp,
                    meta={"ready": ready, "desired": desired},
                ))

        if alerts:
            logger.info(f"AlertingEngine: {len(alerts)} alert(s) detected")
        return alerts


# ── Singleton ──────────────────────────────────────────────────────────────────
alerting_engine = AlertingEngine()
