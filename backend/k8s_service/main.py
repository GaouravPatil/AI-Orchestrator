from fastapi import FastAPI

from k8s_service.app.api.kubernetes import k8s_router

app = FastAPI(
    title="Kubernetes Service"
)

app.include_router(
    k8s_router,
    prefix="/k8s",
    tags=["Kubernetes"]
)