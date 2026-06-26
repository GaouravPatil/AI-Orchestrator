from kubernetes import client, config


class KubernetesClient:

    def __init__(self):
        config.load_kube_config()

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()