from k8s_service.app.kubernetes.client import KubernetesClient


class NamespaceManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_namespaces(self):
        namespaces = self.client.core_v1.list_namespace()

        return [
            {
                "name": ns.metadata.name,
                "status": ns.status.phase,
            }
            for ns in namespaces.items
        ]