"""
Tool functions called by the K8sAgent.
Each function makes an authenticated HTTP call to k8s_service and returns the result.
The bearer token is injected at runtime via set_token() before any tool is called.
"""
import httpx

from ai_service.app.core.config import settings
from ai_service.app.core.logger import logger

# ── Token injection ───────────────────────────────────────────────────────────
# The agent calls set_token(jwt) once per request so every tool call
# carries the user's credentials when forwarded to k8s_service.
_bearer_token: str = ""


def set_token(token: str) -> None:
    global _bearer_token
    _bearer_token = token


def _headers() -> dict:
    return {"Authorization": f"Bearer {_bearer_token}"}


K8S_BASE = settings.K8S_SERVICE_URL.rstrip("/") + "/k8s"


# ── Low-level HTTP helpers ────────────────────────────────────────────────────

def _get(path: str) -> dict:
    url = f"{K8S_BASE}{path}"
    logger.debug(f"k8s_tool GET {url}")
    r = httpx.get(url, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict) -> dict:
    url = f"{K8S_BASE}{path}"
    logger.debug(f"k8s_tool POST {url} body={body}")
    r = httpx.post(url, json=body, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _put(path: str, body: dict) -> dict:
    url = f"{K8S_BASE}{path}"
    logger.debug(f"k8s_tool PUT {url} body={body}")
    r = httpx.put(url, json=body, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _delete(path: str, body: dict) -> dict:
    url = f"{K8S_BASE}{path}"
    logger.debug(f"k8s_tool DELETE {url} body={body}")
    r = httpx.request("DELETE", url, json=body, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


# ── Tool functions (called by the AI agent) ───────────────────────────────────

def list_namespaces() -> dict:
    """List all Kubernetes namespaces."""
    return _get("/namespaces")


def list_nodes() -> dict:
    """List all cluster nodes with their status."""
    return _get("/nodes")


def list_pods() -> dict:
    """List all pods across all namespaces."""
    return _get("/pods")


def list_deployments() -> dict:
    """List all deployments."""
    return _get("/deployments")


def list_services(namespace: str = "default") -> dict:
    """List services in a namespace."""
    return _get(f"/services?namespace={namespace}")


def list_events(namespace: str = "default") -> dict:
    """List recent events in a namespace — useful for diagnosing errors."""
    return _get(f"/events?namespace={namespace}")


def get_pod_logs(namespace: str, pod_name: str, tail: int = 50) -> dict:
    """Fetch the last N log lines from a pod."""
    return _get(f"/pods/{namespace}/{pod_name}/logs?tail={tail}")


def create_deployment(
    name: str, image: str, replicas: int = 1,
    namespace: str = "default", port: int = 80,
) -> dict:
    """Create a new Kubernetes deployment."""
    return _post("/deploy", {
        "name": name,
        "image": image,
        "replicas": replicas,
        "namespace": namespace,
        "container_port": port,
    })


def scale_deployment(name: str, replicas: int, namespace: str = "default") -> dict:
    """Scale a deployment to the specified number of replicas."""
    return _put("/scale", {"name": name, "replicas": replicas, "namespace": namespace})


def delete_deployment(name: str, namespace: str = "default") -> dict:
    """Delete a deployment."""
    return _delete("/deployment", {"name": name, "namespace": namespace})
