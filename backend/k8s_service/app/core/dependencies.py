from functools import lru_cache

from k8s_service.app.kubernetes.client import KubernetesClient


@lru_cache()
def get_kubernetes_client() -> KubernetesClient:
    """
    Returns a singleton Kubernetes client.
    """
    return KubernetesClient()