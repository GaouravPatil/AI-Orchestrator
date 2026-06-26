from k8s_service.app.kubernetes.deployment_manager import DeploymentManager


class OrchestratorRouter:

    def __init__(self):

        self.deployment_manager = DeploymentManager()

    def deployment(self):

        return self.deployment_manager