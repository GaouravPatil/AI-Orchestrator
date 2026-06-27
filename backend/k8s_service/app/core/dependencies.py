from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from shared.security.jwt import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8080/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency — validates JWT and returns the decoded payload.
    Use this in any endpoint that requires authentication.
    """
    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that additionally checks the user has the 'admin' role.
    Use on destructive operations (delete, scale).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user