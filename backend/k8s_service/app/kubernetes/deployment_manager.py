from kubernetes import client

from k8s_service.app.kubernetes.client import KubernetesClient
from k8s_service.app.schemas.deployment import (
    DeploymentRequest,
    ScaleRequest,
    DeleteDeploymentRequest,
)


class DeploymentManager:

    def __init__(self):
        self.client = KubernetesClient()

    # -------------------------------------------------
    # List Deployments
    # -------------------------------------------------

    def list_deployments(self):

        deployments = self.client.apps_v1.list_deployment_for_all_namespaces()

        deployment_list = []

        for deployment in deployments.items:

            image = ""

            if deployment.spec.template.spec.containers:
                image = deployment.spec.template.spec.containers[0].image

            deployment_list.append(
                {
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "replicas": deployment.spec.replicas,
                    "available_replicas": deployment.status.available_replicas or 0,
                    "image": image,
                    "created_at": deployment.metadata.creation_timestamp,
                }
            )

        return deployment_list

    # -------------------------------------------------
    # Create Deployment
    # -------------------------------------------------

    def create_deployment(self, request: DeploymentRequest):

        container = client.V1Container(
            name=request.name,
            image=request.image,
            ports=[
                client.V1ContainerPort(
                    container_port=request.container_port
                )
            ],
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": request.name}
            ),
            spec=client.V1PodSpec(
                containers=[container]
            ),
        )

        spec = client.V1DeploymentSpec(
            replicas=request.replicas,
            selector=client.V1LabelSelector(
                match_labels={"app": request.name}
            ),
            template=template,
        )

        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=request.name
            ),
            spec=spec,
        )

        self.client.apps_v1.create_namespaced_deployment(
            namespace=request.namespace,
            body=deployment,
        )

        return {
            "message": "Deployment created successfully",
            "deployment": request.name,
        }

    # -------------------------------------------------
    # Scale Deployment
    # -------------------------------------------------

    def scale_deployment(self, request: ScaleRequest):

        deployment = self.client.apps_v1.read_namespaced_deployment(
            name=request.name,
            namespace=request.namespace,
        )

        deployment.spec.replicas = request.replicas

        self.client.apps_v1.patch_namespaced_deployment(
            name=request.name,
            namespace=request.namespace,
            body=deployment,
        )

        return {
            "message": "Deployment scaled successfully",
            "replicas": request.replicas,
        }

    # -------------------------------------------------
    # Delete Deployment
    # -------------------------------------------------

    def delete_deployment(self, request: DeleteDeploymentRequest):

        self.client.apps_v1.delete_namespaced_deployment(
            name=request.name,
            namespace=request.namespace,
        )

        return {
            "message": "Deployment deleted successfully",
            "deployment": request.name,
        }