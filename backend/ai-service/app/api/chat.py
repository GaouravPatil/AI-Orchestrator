from fastapi import APIRouter, HTTPException

from ai_service.app.agents.k8s_agent import K8sAgent
from ai_service.app.schemas.chat import ChatRequest, ChatResponse

chat_router = APIRouter()
agent = K8sAgent()


@chat_router.post("/chat", response_model=ChatResponse, summary="Chat with the AI K8s assistant")
def chat(request: ChatRequest):
    try:
        result = agent.chat(
            message=request.message,
            session_id=request.session_id,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/health", summary="AI service health check")
def health():
    return {"status": "running", "model": "llama3"}
