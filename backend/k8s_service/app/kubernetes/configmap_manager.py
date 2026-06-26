from kubernetes import client

from k8s_service.app.kubernetes.client import KubernetesClient


class ConfigMapManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_configmaps(self, namespace: str = "default"):
        cms = self.client.core_v1.list_namespaced_config_map(namespace=namespace)
        return [
            {
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "keys": list(cm.data.keys()) if cm.data else [],
            }
            for cm in cms.items
        ]

    def create_configmap(self, name: str, namespace: str, data: dict):
        body = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=name),
            data=data,
        )
        self.client.core_v1.create_namespaced_config_map(namespace=namespace, body=body)
        return {"message": "ConfigMap created", "configmap": name}

    def delete_configmap(self, name: str, namespace: str = "default"):
        self.client.core_v1.delete_namespaced_config_map(name=name, namespace=namespace)
        return {"message": "ConfigMap deleted", "configmap": name}
