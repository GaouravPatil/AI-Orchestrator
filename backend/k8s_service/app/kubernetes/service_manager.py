from kubernetes import client

from k8s_service.app.kubernetes.client import KubernetesClient


class ServiceManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_services(self, namespace: str = "default"):
        services = self.client.core_v1.list_namespaced_service(namespace=namespace)
        return [
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
        ]

    def get_service(self, name: str, namespace: str = "default"):
        svc = self.client.core_v1.read_namespaced_service(name=name, namespace=namespace)
        return {
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
        }

    def create_service(self, name: str, namespace: str, port: int, target_port: int, selector: dict):
        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1ServiceSpec(
                selector=selector,
                ports=[client.V1ServicePort(port=port, target_port=target_port)],
            ),
        )
        self.client.core_v1.create_namespaced_service(namespace=namespace, body=body)
        return {"message": "Service created", "service": name}

    def delete_service(self, name: str, namespace: str = "default"):
        self.client.core_v1.delete_namespaced_service(name=name, namespace=namespace)
        return {"message": "Service deleted", "service": name}
