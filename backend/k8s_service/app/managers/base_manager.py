from k8s_service.app.core.dependencies import get_kubernetes_client
from k8s_service.app.core.logger import logger
from k8s_service.app.orchestrator.response import ApiResponse


class BaseManager:

    def __init__(self):
        self.client = get_kubernetes_client()
        self.logger = logger

    def success(self, message: str, data=None):
        return ApiResponse.success(message, data)

    def error(self, message: str):
        return ApiResponse.error(message)