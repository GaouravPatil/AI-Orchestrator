"""
ClusterCollector — scrapes k8s_service REST endpoints and stores snapshots
in an in-memory ring buffer.

This is the single source of truth for all monitoring data.
The background task calls collect() on a schedule; the API reads from the buffer.
"""
from collections import deque
from datetime import datetime
from typing import Optional

import httpx

from monitoring_service.app.core.config import settings
from monitoring_service.app.core.logger import logger
from monitoring_service.app.schemas.monitor import (
    ClusterSnapshot,
    DeploymentSnapshot,
    NodeSnapshot,
    PodSnapshot,
)


class ClusterCollector:

    def __init__(self):
        self._history: deque[ClusterSnapshot] = deque(
            maxlen=settings.SNAPSHOT_HISTORY
        )
        self._base = settings.K8S_SERVICE_URL.rstrip("/") + "/k8s"

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def latest(self) -> Optional[ClusterSnapshot]:
        return self._history[-1] if self._history else None

    @property
    def history(self) -> list[ClusterSnapshot]:
        return list(self._history)

    @property
    def history_count(self) -> int:
        return len(self._history)

    # ── Scrape ────────────────────────────────────────────────────────────────

    def collect(self) -> ClusterSnapshot:
        """
        Fetch pods, nodes, and deployments from k8s_service.
        Stores the result in the ring buffer and returns it.
        Errors are captured in the snapshot rather than raised,
        so the service stays alive even if k8s_service is down.
        """
        logger.info("Collecting cluster snapshot...")
        headers = self._auth_headers()

        pods = self._scrape_pods(headers)
        nodes = self._scrape_nodes(headers)
        deployments = self._scrape_deployments(headers)

        error = None
        if pods is None and nodes is None and deployments is None:
            error = "k8s_service unreachable or returned errors for all endpoints"
            logger.warning(error)

        snapshot = ClusterSnapshot(
            timestamp=datetime.utcnow(),
            pods=pods or [],
            nodes=nodes or [],
            deployments=deployments or [],
            scrape_error=error,
        )

        self._history.append(snapshot)
        logger.info(
            f"Snapshot collected — pods={len(snapshot.pods)}, "
            f"nodes={len(snapshot.nodes)}, deployments={len(snapshot.deployments)}"
        )
        return snapshot

    # ── Private helpers ───────────────────────────────────────────────────────

    def _auth_headers(self) -> dict:
        token = settings.INTERNAL_JWT
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _scrape_pods(self, headers: dict) -> Optional[list[PodSnapshot]]:
        try:
            r = httpx.get(f"{self._base}/pods", headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            # k8s_service wraps data in {"status": "success", "data": [...]}
            items = data.get("data", data) if isinstance(data, dict) else data
            return [
                PodSnapshot(
                    namespace=p.get("namespace", ""),
                    name=p.get("name", ""),
                    status=p.get("status"),
                    node=p.get("node"),
                    pod_ip=p.get("pod_ip"),
                    restarts=p.get("restarts", 0) or 0,
                )
                for p in (items if isinstance(items, list) else [])
            ]
        except Exception as e:
            logger.warning(f"Failed to scrape pods: {e}")
            return None

    def _scrape_nodes(self, headers: dict) -> Optional[list[NodeSnapshot]]:
        try:
            r = httpx.get(f"{self._base}/nodes", headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            items = data.get("data", data) if isinstance(data, dict) else data
            return [
                NodeSnapshot(
                    name=n.get("name", ""),
                    status=n.get("status", "Unknown"),
                    roles=n.get("roles", []) or [],
                    cpu=n.get("cpu"),
                    memory=n.get("memory"),
                )
                for n in (items if isinstance(items, list) else [])
            ]
        except Exception as e:
            logger.warning(f"Failed to scrape nodes: {e}")
            return None

    def _scrape_deployments(self, headers: dict) -> Optional[list[DeploymentSnapshot]]:
        try:
            r = httpx.get(f"{self._base}/deployments", headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            items = data.get("data", data) if isinstance(data, dict) else data
            return [
                DeploymentSnapshot(
                    namespace=d.get("namespace", ""),
                    name=d.get("name", ""),
                    replicas=d.get("replicas"),
                    ready_replicas=d.get("ready_replicas"),
                )
                for d in (items if isinstance(items, list) else [])
            ]
        except Exception as e:
            logger.warning(f"Failed to scrape deployments: {e}")
            return None


# ── Singleton used by the rest of the service ─────────────────────────────────
collector = ClusterCollector()
