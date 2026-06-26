from pydantic import BaseModel, Field


class DeploymentRequest(BaseModel):
    name: str
    image: str
    replicas: int = Field(default=1, ge=1)
    namespace: str = "default"
    container_port: int = 80


class ScaleRequest(BaseModel):
    name: str
    replicas: int = Field(..., ge=0)
    namespace: str = "default"


class DeleteDeploymentRequest(BaseModel):
    name: str
    namespace: str = "default"