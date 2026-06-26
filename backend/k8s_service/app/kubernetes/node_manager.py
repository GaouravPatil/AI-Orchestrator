from k8s_service.app.managers.base_manager import BaseManager


class NodeManager(BaseManager):

    def __init__(self):
        super().__init__()

    def list_nodes(self):

        self.logger.info("Fetching cluster nodes")

        nodes = self.client.core_v1.list_node()

        node_list = []

        for node in nodes.items:

            roles = "worker"

            labels = node.metadata.labels or {}

            if "node-role.kubernetes.io/control-plane" in labels:
                roles = "control-plane"

            node_list.append(
                {
                    "name": node.metadata.name,
                    "status": node.status.conditions[-1].type if node.status.conditions else "Unknown",
                    "role": roles,
                    "kubelet_version": node.status.node_info.kubelet_version,
                    "os": node.status.node_info.operating_system,
                    "architecture": node.status.node_info.architecture,
                }
            )

        return self.success("Nodes fetched successfully", node_list)