from kubernetes import client

from k8s_service.app.kubernetes.client import KubernetesClient


class JobManager:

    def __init__(self):
        self.client = KubernetesClient()

    def list_jobs(self, namespace: str = "default"):
        jobs = self.client.batch_v1.list_namespaced_job(namespace=namespace)
        return [
            {
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "active": job.status.active or 0,
                "succeeded": job.status.succeeded or 0,
                "failed": job.status.failed or 0,
                "start_time": job.status.start_time,
                "completion_time": job.status.completion_time,
            }
            for job in jobs.items
        ]

    def create_job(self, name: str, namespace: str, image: str, command: list):
        container = client.V1Container(name=name, image=image, command=command)
        template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(containers=[container], restart_policy="Never")
        )
        spec = client.V1JobSpec(template=template)
        body = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec,
        )
        self.client.batch_v1.create_namespaced_job(namespace=namespace, body=body)
        return {"message": "Job created", "job": name}

    def delete_job(self, name: str, namespace: str = "default"):
        self.client.batch_v1.delete_namespaced_job(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(propagation_policy="Foreground"),
        )
        return {"message": "Job deleted", "job": name}
