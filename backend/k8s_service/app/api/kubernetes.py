from fastapi import APIRouter

from k8s_service.app.kubernetes.pod_manager import PodManager
from k8s_service.app.kubernetes.namespace_manager import NamespaceManager
from k8s_service.app.kubernetes.node_manager import NodeManager
from k8s_service.app.kubernetes.deployment_manager import DeploymentManager
from k8s_service.app.orchestrator.executor import OrchestratorExecutor

from k8s_service.app.schemas.deployment import (
    DeploymentRequest,
    ScaleRequest,
    DeleteDeploymentRequest,
)

k8s_router = APIRouter()

namespace_manager = NamespaceManager()
pod_manager = PodManager()
node_manager = NodeManager()
deployment_manager = DeploymentManager()
executor = OrchestratorExecutor()

@k8s_router.get("/namespaces")
def get_namespaces():
    return namespace_manager.list_namespaces()


@k8s_router.get("/nodes")
def get_nodes():
    return node_manager.list_nodes()


@k8s_router.get("/pods")
def get_pods():
    return pod_manager.list_pods()


@k8s_router.get("/deployments")
def get_deployments():
    return executor.list_deployments()



@k8s_router.post("/deploy")
def deploy(request: DeploymentRequest):
    return executor.create_deployment(request)


@k8s_router.put("/scale")
def scale(request: ScaleRequest):
    return executor.scale_deployment(request)


@k8s_router.delete("/deployment")
def delete(request: DeleteDeploymentRequest):
    return executor.delete_deployment(request)