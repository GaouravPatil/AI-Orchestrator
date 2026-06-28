from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.database.base import Base
from shared.database.session import engine
from auth_service.app.api.auth import auth_router
from auth_service.app.models.user import User  

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth Service",
    description="Authentication and user management for AI DevOps Orchestrator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"service": "auth-service", "status": "running", "docs": "/docs"}


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])