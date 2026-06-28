from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer

from shared.core.config import settings
from shared.security.jwt import verify_access_token

# OAuth2PasswordBearer points to the /token endpoint on THIS service.
# This makes Swagger UI show a username + password form on "Authorize".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

# HTTPBearer is a fallback for clients that send a raw Bearer header
# without going through the OAuth2 form (e.g. curl, other services).
_http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    oauth2_token: str | None = Depends(oauth2_scheme),
    bearer: HTTPAuthorizationCredentials | None = Security(_http_bearer),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """
    Triple-mode auth dependency (checked in order):

    1. OAuth2 Password flow token  — Swagger "Authorize" username/password form
    2. Raw Bearer JWT              — curl / programmatic clients
    3. X-API-Key header            — service-to-service / scripts (static key)
    """
    # ── 1 & 2: JWT (from either oauth2 form or raw Bearer header) ─────────────
    token = oauth2_token or (bearer.credentials if bearer else None)
    if token:
        payload = verify_access_token(token)
        if payload is not None:
            return payload

    # ── 3. Static API key ──────────────────────────────────────────────────────
    if x_api_key and x_api_key == settings.INTERNAL_API_KEY:
        return {"sub": "internal-service", "role": "admin"}

    # ── Nothing matched ────────────────────────────────────────────────────────
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide valid credentials via /token, a Bearer JWT, or X-API-Key header",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that additionally checks the user has the 'admin' role.
    Use on destructive operations (delete, scale).
    API-key callers are implicitly granted admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user