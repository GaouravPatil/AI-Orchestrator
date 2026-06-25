from kubernetes import client, config


class KubernetesClient:

    def __init__(self):
        config.load_kube_config()

        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()