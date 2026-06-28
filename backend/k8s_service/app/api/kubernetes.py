# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends

from k8s_service.app.core.dependencies import get_current_user, require_admin
from k8s_service.app.kubernetes.pod_manager import PodManager
from k8s_service.app.kubernetes.namespace_manager import NamespaceManager
from k8s_service.app.kubernetes.node_manager import NodeManager
from k8s_service.app.kubernetes.deployment_manager import DeploymentManager
from k8s_service.app.kubernetes.service_manager import ServiceManager
from k8s_service.app.kubernetes.event_manager import EventManager
from k8s_service.app.kubernetes.log_manager import LogManager
from k8s_service.app.orchestrator.executor import OrchestratorExecutor

from k8s_service.app.schemas.deployment import (
    DeploymentRequest,
    ScaleRequest,
    DeleteDeploymentRequest,
)
from k8s_service.app.schemas.service import ServiceRequest, DeleteServiceRequest

k8s_router = APIRouter(dependencies=[Depends(get_current_user)])

# Managers (singleton-style — one per process)
namespace_manager = NamespaceManager()
pod_manager = PodManager()
node_manager = NodeManager()
service_manager = ServiceManager()
event_manager = EventManager()
log_manager = LogManager()

# Orchestrator (validates + audits before calling managers)
executor = OrchestratorExecutor()


# ─────────────────────────────────────────
# Cluster Info  (read-only — any auth user)
# ─────────────────────────────────────────

@k8s_router.get("/namespaces", summary="List all namespaces")
def get_namespaces():
    return namespace_manager.list_namespaces()


@k8s_router.get("/nodes", summary="List cluster nodes")
def get_nodes():
    return node_manager.list_nodes()


@k8s_router.get("/events", summary="List events in a namespace")
def get_events(namespace: str = "default"):
    return event_manager.list_events(namespace=namespace)


# ─────────────────────────────────────────
# Pods  (read-only)
# ─────────────────────────────────────────

@k8s_router.get("/pods", summary="List all pods across all namespaces")
def get_pods():
    return pod_manager.list_pods()


@k8s_router.get("/pods/{namespace}/{pod_name}/logs", summary="Get pod logs")
def get_pod_logs(namespace: str, pod_name: str, tail: int = 100):
    return log_manager.get_pod_logs(
        pod_name=pod_name,
        namespace=namespace,
        tail_lines=tail,
    )


# ─────────────────────────────────────────
# Deployments  (mutating — admin only)
# ─────────────────────────────────────────

@k8s_router.get("/deployments", summary="List all deployments")
def get_deployments():
    return executor.list_deployments()


@k8s_router.post(
    "/deploy",
    summary="Create a deployment",
    dependencies=[Depends(require_admin)],
)
def deploy(request: DeploymentRequest):
    return executor.create_deployment(request)


@k8s_router.put(
    "/scale",
    summary="Scale a deployment",
    dependencies=[Depends(require_admin)],
)
def scale(request: ScaleRequest):
    return executor.scale_deployment(request)


@k8s_router.delete(
    "/deployment",
    summary="Delete a deployment",
    dependencies=[Depends(require_admin)],
)
def delete_deployment(request: DeleteDeploymentRequest):
    return executor.delete_deployment(request)


# ─────────────────────────────────────────
# Services  (list = any user, mutate = admin)
# ─────────────────────────────────────────

@k8s_router.get("/services", summary="List services in a namespace")
def list_services(namespace: str = "default"):
    return service_manager.list_services(namespace=namespace)


@k8s_router.get("/services/{namespace}/{name}", summary="Get a specific service")
def get_service(namespace: str, name: str):
    return service_manager.get_service(name=name, namespace=namespace)


@k8s_router.post(
    "/services",
    summary="Create a service",
    dependencies=[Depends(require_admin)],
)
def create_service(request: ServiceRequest):
    return service_manager.create_service(request)


@k8s_router.delete(
    "/services",
    summary="Delete a service",
    dependencies=[Depends(require_admin)],
)
def delete_service(request: DeleteServiceRequest):
    return service_manager.delete_service(request)