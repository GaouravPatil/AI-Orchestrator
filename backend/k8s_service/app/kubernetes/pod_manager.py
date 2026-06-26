from k8s_service.app.managers.base_manager import BaseManager


class PodManager(BaseManager):

    def __init__(self):
        super().__init__()

    def list_pods(self):

        self.logger.info("Fetching pods from all namespaces")

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

        return self.success("Pods fetched successfully", pod_list)