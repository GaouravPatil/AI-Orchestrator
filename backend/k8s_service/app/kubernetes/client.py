from kubernetes import client, config
from pathlib import Path

from k8s_service.app.core.config import settings


class KubernetesClient:

    def __init__(self):

        kubeconfig = Path(settings.KUBECONFIG_PATH).expanduser()

        config.load_kube_config(
            config_file=str(kubeconfig)
        )

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()