from fastapi import Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.core.config import settings
from shared.security.jwt import verify_access_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """Dual-mode auth: Bearer JWT or X-API-Key header."""
    if credentials is not None:
        payload = verify_access_token(credentials.credentials)
        if payload is not None:
            return payload

    if x_api_key and x_api_key == settings.INTERNAL_API_KEY:
        return {"sub": "internal-service", "role": "admin"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide a valid Bearer token or X-API-Key header",
        headers={"WWW-Authenticate": "Bearer"},
    )
