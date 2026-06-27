from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from shared.security.jwt import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8080/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency — validates JWT and returns the decoded payload.
    Mirrors the same guard used in k8s_service.
    """
    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_bearer_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    Returns the raw JWT string so it can be forwarded to k8s_service
    in Authorization headers for tool calls.
    """
    return token
