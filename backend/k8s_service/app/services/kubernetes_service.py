from k8s_service.app.kubernetes.client import KubernetesClient


class KubernetesService:

    def __init__(self):
        self.client = KubernetesClient()

    def list_namespaces(self):
        namespaces = self.client.core.list_namespace()
        return [
            {
                "name": ns.metadata.name,
                "status": ns.status.phase,
            }
            for ns in namespaces.items
        ]

    def list_services(self, namespace: str = "default"):
        services = self.client.core.list_namespaced_service(namespace=namespace)
        return [
            {
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "ports": [
                    {"port": p.port, "protocol": p.protocol, "target_port": str(p.target_port)}
                    for p in (svc.spec.ports or [])
                ],
            }
            for svc in services.items
        ]

    def get_service(self, name: str, namespace: str = "default"):
        svc = self.client.core.read_namespaced_service(name=name, namespace=namespace)
        return {
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type,
            "cluster_ip": svc.spec.cluster_ip,
            "ports": [
                {"port": p.port, "protocol": p.protocol, "target_port": str(p.target_port)}
                for p in (svc.spec.ports or [])
            ],
            "selector": svc.spec.selector,
        }

    def list_pods(self, namespace: str = "default"):
        pods = self.client.core.list_namespaced_pod(namespace=namespace)
        return [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
            }
            for pod in pods.items
        ]

    def list_deployments(self, namespace: str = "default"):
        deployments = self.client.apps.list_namespaced_deployment(namespace=namespace)
        return [
            {
                "name": d.metadata.name,
                "namespace": d.metadata.namespace,
                "replicas": d.spec.replicas,
                "ready_replicas": d.status.ready_replicas,
            }
            for d in deployments.items
        ]