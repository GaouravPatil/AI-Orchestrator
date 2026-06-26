from k8s_service.app.managers.base_manager import BaseManager


class NamespaceManager(BaseManager):

    def __init__(self):
        super().__init__()

    def list_namespaces(self):

        self.logger.info("Fetching namespaces")

        namespaces = self.client.core_v1.list_namespace()

        data = [
            {
                "name": ns.metadata.name,
                "status": ns.status.phase,
            }
            for ns in namespaces.items
        ]

        return self.success(
            "Namespaces fetched successfully",
            data
        )