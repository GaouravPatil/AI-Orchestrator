# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status


class K8sResourceNotFound(HTTPException):
    def __init__(self, resource: str, name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} '{name}' not found",
        )


class K8sConflict(HTTPException):
    def __init__(self, resource: str, name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} '{name}' already exists",
        )


class K8sValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        )


class K8sConnectionError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to the Kubernetes cluster",
        )
