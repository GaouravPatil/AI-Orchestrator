from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.core.config import settings
from shared.security.jwt import verify_access_token

# HTTPBearer is used for Swagger "Authorize" button (Bearer JWT)
# auto_error=False so we can fall through to API-key check
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """
    Dual-mode auth dependency:
      1. Bearer JWT — full user payload returned (for user-facing requests)
      2. X-API-Key  — static internal key (for service-to-service / scripts)
    """
    # ── 1. Try Bearer JWT ──────────────────────────────────────────────────────
    if credentials is not None:
        payload = verify_access_token(credentials.credentials)
        if payload is not None:
            return payload

    # ── 2. Try static API key ──────────────────────────────────────────────────
    if x_api_key and x_api_key == settings.INTERNAL_API_KEY:
        return {"sub": "internal-service", "role": "admin"}

    # ── Nothing matched ────────────────────────────────────────────────────────
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide a valid Bearer token or X-API-Key header",
        headers={"WWW-Authenticate": "Bearer"},
    )
