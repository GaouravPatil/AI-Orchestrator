"""
Chat schemas for the AI service — Pydantic v2.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: Role
    content: str
    tool_call_id: Optional[str] = None     # set when role == TOOL
    name: Optional[str] = None             # tool name (for tool result messages)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    conversation_id: Optional[str] = None
    namespace: str = "default"             # default k8s namespace context
    history: list[ChatMessage] = Field(default_factory=list)

    model_config = {"json_schema_extra": {"example": {
        "message": "How many pods are running in the default namespace?",
        "namespace": "default",
    }}}


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class AgentStep(BaseModel):
    """One iteration of the agent's think → act loop (for debug / tracing)."""
    iteration: int
    thought: Optional[str] = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    namespace: str
    steps: list[AgentStep] = Field(default_factory=list)   # full agentic trace
    model: str
    provider: str = "ollama"
    total_tokens: Optional[int] = None
