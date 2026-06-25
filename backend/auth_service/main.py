from fastapi import FastAPI

from shared.database.base import Base
from shared.database.session import engine
from auth_service.app.api.auth import auth_router


# Import models
from auth_service.app.models.user import User

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth Service"
)


@app.get("/")
def home():
    return {
        "status": "running"
    }

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)