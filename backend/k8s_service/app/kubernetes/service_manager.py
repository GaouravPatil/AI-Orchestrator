from kubernetes import client

from k8s_service.app.managers.base_manager import BaseManager
from k8s_service.app.schemas.service import ServiceRequest, DeleteServiceRequest


class ServiceManager(BaseManager):

    def __init__(self):
        super().__init__()

    def list_services(self, namespace: str = "default"):

        self.logger.info(f"Listing services in namespace '{namespace}'")

        services = self.client.core_v1.list_namespaced_service(namespace=namespace)

        return self.success(
            "Services fetched successfully",
            [
                {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "ports": [
                        {
                            "port": p.port,
                            "protocol": p.protocol,
                            "target_port": str(p.target_port),
                        }
                        for p in (svc.spec.ports or [])
                    ],
                }
                for svc in services.items
            ],
        )

    def get_service(self, name: str, namespace: str = "default"):

        self.logger.info(f"Getting service '{name}' in namespace '{namespace}'")

        svc = self.client.core_v1.read_namespaced_service(name=name, namespace=namespace)

        return self.success(
            "Service fetched successfully",
            {
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "ports": [
                    {
                        "port": p.port,
                        "protocol": p.protocol,
                        "target_port": str(p.target_port),
                    }
                    for p in (svc.spec.ports or [])
                ],
                "selector": svc.spec.selector,
            },
        )

    def create_service(self, request: ServiceRequest):

        self.logger.info(f"Creating service '{request.name}' in '{request.namespace}'")

        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=request.name),
            spec=client.V1ServiceSpec(
                type=request.service_type,
                selector=request.selector,
                ports=[
                    client.V1ServicePort(
                        port=request.port,
                        target_port=request.target_port,
                    )
                ],
            ),
        )

        self.client.core_v1.create_namespaced_service(
            namespace=request.namespace,
            body=body,
        )

        return self.success(
            "Service created successfully",
            {"service": request.name, "namespace": request.namespace},
        )

    def delete_service(self, request: DeleteServiceRequest):

        self.logger.info(f"Deleting service '{request.name}' from '{request.namespace}'")

        self.client.core_v1.delete_namespaced_service(
            name=request.name,
            namespace=request.namespace,
        )

        return self.success(
            "Service deleted successfully",
            {"service": request.name, "namespace": request.namespace},
        )
