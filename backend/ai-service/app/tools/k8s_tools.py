import httpx


K8S_BASE = "http://localhost:8001/k8s"


def _get(path: str) -> dict:
    r = httpx.get(f"{K8S_BASE}{path}", timeout=10)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict) -> dict:
    r = httpx.post(f"{K8S_BASE}{path}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def _put(path: str, body: dict) -> dict:
    r = httpx.put(f"{K8S_BASE}{path}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def _delete(path: str, body: dict) -> dict:
    r = httpx.request("DELETE", f"{K8S_BASE}{path}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()


# ─── Tool functions (called by the AI agent) ─────────────────────────────────

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
    """List all deployments across all namespaces."""
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


def create_deployment(name: str, image: str, replicas: int = 1,
                      namespace: str = "default", port: int = 80) -> dict:
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
