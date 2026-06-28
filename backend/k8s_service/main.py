# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from k8s_service.app.api.kubernetes import k8s_router

app = FastAPI(
    title="Kubernetes Service",
    description="Kubernetes cluster management API for AI DevOps Orchestrator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(k8s_router, prefix="/k8s", tags=["Kubernetes"])


@app.get("/")
def root():
    return {"service": "k8s-service", "message": "Kubernetes Service Running", "docs": "/docs"}