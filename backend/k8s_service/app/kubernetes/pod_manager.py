from k8s_service.app.kubernetes.client import KubernetesClient


class PodManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_pods(self):

        pods = self.client.core_v1.list_pod_for_all_namespaces()

        pod_list = []

        for pod in pods.items:

            restart_count = 0

            if pod.status.container_statuses:
                restart_count = sum(
                    c.restart_count for c in pod.status.container_statuses
                )

            pod_list.append(
                {
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "pod_ip": pod.status.pod_ip,
                    "restarts": restart_count,
                }
            )

        return pod_list