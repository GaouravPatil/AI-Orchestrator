from fastapi import APIRouter, Depends, HTTPException

from ai_service.app.agents.k8s_agent import K8sAgent
from ai_service.app.core.dependencies import get_current_user, get_bearer_token
from ai_service.app.core.logger import logger
from ai_service.app.schemas.chat import ChatRequest, ChatResponse

chat_router = APIRouter()
agent = K8sAgent()


@chat_router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with the AI K8s assistant",
    dependencies=[Depends(get_current_user)],
)
def chat(
    request: ChatRequest,
    token: str = Depends(get_bearer_token),
):
    """
    Send a natural language message to the AI Kubernetes assistant.
    The agent will reason about the request, call k8s_service tools as needed,
    and return a human-readable answer with a full step trace.
    """
    try:
        logger.info(f"Chat request — conversation_id={request.conversation_id}, ns={request.namespace}")
        result = agent.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            namespace=request.namespace,
            bearer_token=token,
        )
        return ChatResponse(**result)
    except RuntimeError as e:
        # Structured errors from OllamaService / k8s_tools
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in /ai/chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@chat_router.get("/health", summary="AI service health check")
def health():
    return {
        "status": "running",
        "model": agent.llm.model,
        "provider": "ollama",
    }
