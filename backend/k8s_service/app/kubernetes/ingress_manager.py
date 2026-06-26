from kubernetes import client

from k8s_service.app.kubernetes.client import KubernetesClient


class IngressManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_ingresses(self, namespace: str = "default"):
        ingresses = self.client.networking_v1.list_namespaced_ingress(namespace=namespace)
        return [
            {
                "name": ing.metadata.name,
                "namespace": ing.metadata.namespace,
                "rules": [
                    {
                        "host": rule.host,
                        "paths": [
                            {
                                "path": p.path,
                                "backend_service": p.backend.service.name,
                                "backend_port": p.backend.service.port.number,
                            }
                            for p in (rule.http.paths if rule.http else [])
                        ],
                    }
                    for rule in (ing.spec.rules or [])
                ],
            }
            for ing in ingresses.items
        ]
