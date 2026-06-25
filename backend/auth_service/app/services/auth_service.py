from typing import Any

from sqlalchemy.orm import Session

from auth_service.app.models.user import User

from auth_service.app.schemas.user import UserRegister

from shared.security.jwt import create_access_token
from shared.security.password import hash_password, verify_password


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserRegister) -> User:
        """Register a new user."""

        existing_user = (
            self.db.query(User)
            .filter(User.email == user_data.email)
            .first()
        )

        if existing_user:
            raise ValueError("Email already exists")

        user = User(
            name=user_data.name,
            email=user_data.email,
            password=hash_password(user_data.password),
            role="viewer",
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def login_user(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user and generate a JWT access token."""

        user = (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

        if user is None:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user.password):
            raise ValueError("Invalid email or password")

        access_token = create_access_token(
            {
                "sub": user.email,
                "role": user.role,
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }