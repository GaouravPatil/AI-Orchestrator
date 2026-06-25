from fastapi import APIRouter

from k8s_service.app.services.kubernetes_service import KubernetesService

k8s_router = APIRouter()

service = KubernetesService()


@k8s_router.get("/namespaces")
def get_namespaces():
    return service.list_namespaces()