from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from auth_service.app.schemas.user import UserLogin, UserRegister, UserResponse
from auth_service.app.services.auth_service import AuthService
from shared.database.session import get_db
from shared.security.jwt import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_router = APIRouter()


@auth_router.get("/")
def auth_home():
    return {"message": "Authentication Service"}

@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    service = AuthService(db)

    try:
        return service.register_user(user)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@auth_router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    service = AuthService(db)

    try:
        return service.login_user(
            user.email,
            user.password
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

@auth_router.get("/me")
def me(
    token: str = Depends(oauth2_scheme),
):

    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    return payload