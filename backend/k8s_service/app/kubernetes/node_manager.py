from k8s_service.app.kubernetes.client import KubernetesClient


class NodeManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_nodes(self):

        nodes = self.client.core_v1.list_node()

        node_list = []

        for node in nodes.items:

            roles = "worker"

            labels = node.metadata.labels

            if "node-role.kubernetes.io/control-plane" in labels:
                roles = "control-plane"

            node_list.append(
                {
                    "name": node.metadata.name,
                    "status": node.status.conditions[-1].type,
                    "role": roles,
                    "kubelet_version": node.status.node_info.kubelet_version,
                    "os": node.status.node_info.operating_system,
                    "architecture": node.status.node_info.architecture,
                }
            )

        return node_list