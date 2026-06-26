from k8s_service.app.kubernetes.client import KubernetesClient


class EventManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_events(self, namespace: str = "default"):
        events = self.client.core_v1.list_namespaced_event(namespace=namespace)
        return [
            {
                "name": e.metadata.name,
                "namespace": e.metadata.namespace,
                "reason": e.reason,
                "message": e.message,
                "type": e.type,
                "count": e.count,
                "involved_object": e.involved_object.name,
                "involved_kind": e.involved_object.kind,
                "first_time": e.first_timestamp,
                "last_time": e.last_timestamp,
            }
            for e in events.items
        ]
