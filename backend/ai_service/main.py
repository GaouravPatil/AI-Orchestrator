from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_service.app.api.chat import chat_router

app = FastAPI(
    title="AI DevOps Assistant",
    description="Natural language interface for Kubernetes cluster management",
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
def root():
    return {"service": "ai-service", "message": "AI Service Running", "docs": "/docs"}


app.include_router(chat_router, prefix="/ai", tags=["AI Assistant"])
