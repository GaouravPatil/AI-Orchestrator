from fastapi import FastAPI

from ai_service.app.api.chat import chat_router

app = FastAPI(
    title="AI DevOps Assistant",
    description="Natural language interface for Kubernetes cluster management",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "AI Service Running", "docs": "/docs"}


app.include_router(
    chat_router,
    prefix="/ai",
    tags=["AI Assistant"],
)
