from kubernetes import client

from k8s_service.app.managers.base_manager import BaseManager
from k8s_service.app.schemas.deployment import (
    DeploymentRequest,
    ScaleRequest,
    DeleteDeploymentRequest,
)


class DeploymentManager(BaseManager):

    def __init__(self):
        super().__init__()

    # -------------------------------------------------
    # List Deployments
    # -------------------------------------------------

    def list_deployments(self):

        self.logger.info("Fetching deployments from Kubernetes")

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

        return self.success(
            "Deployments fetched successfully",
            deployment_list,
        )

    # -------------------------------------------------
    # Create Deployment
    # -------------------------------------------------

    def create_deployment(self, request: DeploymentRequest):

        self.logger.info(
            f"Creating deployment '{request.name}' "
            f"in namespace '{request.namespace}'"
        )

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

        self.logger.info(
            f"Deployment '{request.name}' created successfully."
        )

        return self.success(
            "Deployment created successfully",
            {
                "deployment": request.name,
                "namespace": request.namespace,
                "replicas": request.replicas,
            },
        )

    # -------------------------------------------------
    # Scale Deployment
    # -------------------------------------------------

    def scale_deployment(self, request: ScaleRequest):

        self.logger.info(
            f"Scaling deployment '{request.name}' "
            f"to {request.replicas} replicas."
        )

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

        self.logger.info(
            f"Deployment '{request.name}' scaled successfully."
        )

        return self.success(
            "Deployment scaled successfully",
            {
                "deployment": request.name,
                "namespace": request.namespace,
                "replicas": request.replicas,
            },
        )

    # -------------------------------------------------
    # Delete Deployment
    # -------------------------------------------------

    def delete_deployment(self, request: DeleteDeploymentRequest):

        self.logger.info(
            f"Deleting deployment '{request.name}' "
            f"from namespace '{request.namespace}'"
        )

        self.client.apps_v1.delete_namespaced_deployment(
            name=request.name,
            namespace=request.namespace,
        )

        self.logger.info(
            f"Deployment '{request.name}' deleted successfully."
        )

        return self.success(
            "Deployment deleted successfully",
            {
                "deployment": request.name,
                "namespace": request.namespace,
            },
        )