import base64

from kubernetes import client

from k8s_service.app.kubernetes.client import KubernetesClient


class SecretManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_secrets(self, namespace: str = "default"):
        secrets = self.client.core_v1.list_namespaced_secret(namespace=namespace)
        return [
            {
                "name": s.metadata.name,
                "namespace": s.metadata.namespace,
                "type": s.type,
                "keys": list(s.data.keys()) if s.data else [],
            }
            for s in secrets.items
        ]

    def create_secret(self, name: str, namespace: str, data: dict):
        encoded = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}
        body = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(name=name),
            data=encoded,
        )
        self.client.core_v1.create_namespaced_secret(namespace=namespace, body=body)
        return {"message": "Secret created", "secret": name}

    def delete_secret(self, name: str, namespace: str = "default"):
        self.client.core_v1.delete_namespaced_secret(name=name, namespace=namespace)
        return {"message": "Secret deleted", "secret": name}
