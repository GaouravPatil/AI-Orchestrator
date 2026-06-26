from k8s_service.app.kubernetes.client import KubernetesClient


class LogManager:

    def __init__(self):
        self.client = KubernetesClient()

    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: str = None,
        tail_lines: int = 100,
    ) -> str:
        logs = self.client.core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
        )
        return logs
