from kubernetes import client

from k8s_service.app.kubernetes.client import KubernetesClient


class PVCManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_pvcs(self, namespace: str = "default"):
        pvcs = self.client.core_v1.list_namespaced_persistent_volume_claim(namespace=namespace)
        return [
            {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase,
                "capacity": pvc.status.capacity,
                "access_modes": pvc.spec.access_modes,
                "storage_class": pvc.spec.storage_class_name,
            }
            for pvc in pvcs.items
        ]

    def create_pvc(self, name: str, namespace: str, storage: str, access_modes: list, storage_class: str = None):
        resources = client.V1ResourceRequirements(requests={"storage": storage})
        spec = client.V1PersistentVolumeClaimSpec(
            access_modes=access_modes,
            resources=resources,
            storage_class_name=storage_class,
        )
        body = client.V1PersistentVolumeClaim(
            api_version="v1",
            kind="PersistentVolumeClaim",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec,
        )
        self.client.core_v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=body)
        return {"message": "PVC created", "pvc": name}

    def delete_pvc(self, name: str, namespace: str = "default"):
        self.client.core_v1.delete_namespaced_persistent_volume_claim(name=name, namespace=namespace)
        return {"message": "PVC deleted", "pvc": name}
