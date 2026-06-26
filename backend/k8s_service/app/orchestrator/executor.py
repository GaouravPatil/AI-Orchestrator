from k8s_service.app.orchestrator.audit import AuditLogger
from k8s_service.app.orchestrator.router import OrchestratorRouter
from k8s_service.app.orchestrator.validator import RequestValidator


class OrchestratorExecutor:

    def __init__(self):
        self.router = OrchestratorRouter()

    def list_deployments(self):
        AuditLogger.log("LIST_DEPLOYMENTS", "all")
        return self.router.deployment().list_deployments()

    def create_deployment(self, request):
        RequestValidator.validate_name(request.name)
        RequestValidator.validate_namespace(request.namespace)
        AuditLogger.log("CREATE_DEPLOYMENT", request.name)
        return self.router.deployment().create_deployment(request)

    def scale_deployment(self, request):
        RequestValidator.validate_name(request.name)
        RequestValidator.validate_namespace(request.namespace)
        AuditLogger.log("SCALE_DEPLOYMENT", request.name)
        return self.router.deployment().scale_deployment(request)

    def delete_deployment(self, request):
        RequestValidator.validate_name(request.name)
        RequestValidator.validate_namespace(request.namespace)
        AuditLogger.log("DELETE_DEPLOYMENT", request.name)
        return self.router.deployment().delete_deployment(request)