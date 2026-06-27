from pydantic import BaseModel, Field


class ServiceRequest(BaseModel):
    name: str
    namespace: str = "default"

    # Pod labels to select
    selector: dict[str, str]

    port: int = Field(default=80, ge=1)
    target_port: int = Field(default=80, ge=1)

    service_type: str = "ClusterIP"


class DeleteServiceRequest(BaseModel):
    name: str
    namespace: str = "default"