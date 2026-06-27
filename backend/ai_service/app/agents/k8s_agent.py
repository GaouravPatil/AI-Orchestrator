"""
K8sAgent — multi-turn agentic loop for Kubernetes operations.

Flow per user message:
  1. Append user message to conversation history.
  2. Ask the LLM.
  3. If the LLM returns a JSON {"thought", "action", "params"} block → call the tool,
     append the tool result, ask the LLM again.
  4. Repeat up to MAX_TOOL_ITERATIONS times.
  5. Return the final natural-language answer + full step trace.
"""
import json
import uuid
from typing import Optional

from ai_service.app.core.config import settings
from ai_service.app.core.logger import logger
from ai_service.app.schemas.chat import AgentStep, ToolCall
from ai_service.app.services.ollama_service import OllamaService
from ai_service.app.tools import k8s_tools

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI DevOps assistant for a Kubernetes cluster.
You help users query and manage their cluster using natural language.

When you need to take an action, respond ONLY with a valid JSON block like this:
{
  "thought": "Brief reasoning about why you're calling this tool",
  "action": "tool_name",
  "params": { "key": "value" }
}

Available tools:
- list_namespaces()
- list_nodes()
- list_pods()
- list_deployments()
- list_services(namespace)
- list_events(namespace)
- get_pod_logs(namespace, pod_name, tail=50)
- create_deployment(name, image, replicas, namespace, port)
- scale_deployment(name, replicas, namespace)
- delete_deployment(name, namespace)

If you don't need to call a tool, respond naturally in plain text.
Always be concise, accurate, and helpful.
"""

# ── Tool registry ─────────────────────────────────────────────────────────────

TOOL_MAP: dict = {
    "list_namespaces":   k8s_tools.list_namespaces,
    "list_nodes":        k8s_tools.list_nodes,
    "list_pods":         k8s_tools.list_pods,
    "list_deployments":  k8s_tools.list_deployments,
    "list_services":     k8s_tools.list_services,
    "list_events":       k8s_tools.list_events,
    "get_pod_logs":      k8s_tools.get_pod_logs,
    "create_deployment": k8s_tools.create_deployment,
    "scale_deployment":  k8s_tools.scale_deployment,
    "delete_deployment": k8s_tools.delete_deployment,
}

# ── In-memory session store (replace with Redis in production) ────────────────

_sessions: dict[str, list[dict]] = {}


class K8sAgent:

    def __init__(self):
        self.llm = OllamaService()
        self.max_iterations = settings.MAX_TOOL_ITERATIONS

    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        namespace: str = "default",
        bearer_token: Optional[str] = None,
    ) -> dict:
        """
        Run the agentic loop for a single user message.

        Args:
            message:         The user's natural language message.
            conversation_id: Session ID for conversation continuity.
            namespace:       Default k8s namespace context.
            bearer_token:    JWT to forward to k8s_service tool calls.

        Returns:
            dict with keys: conversation_id, answer, namespace, steps, model, provider
        """
        # ── Setup ──────────────────────────────────────────────────────────
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        if bearer_token:
            k8s_tools.set_token(bearer_token)

        if conversation_id not in _sessions:
            _sessions[conversation_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        history = _sessions[conversation_id]

        # Trim history to stay within window
        max_msgs = settings.MAX_HISTORY_MESSAGES
        if len(history) > max_msgs:
            history = [history[0]] + history[-(max_msgs - 1):]

        history.append({"role": "user", "content": message})

        # ── Agentic loop ───────────────────────────────────────────────────
        steps: list[AgentStep] = []
        answer = ""

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"[{conversation_id}] Agent iteration {iteration}")

            raw_reply = self.llm.chat(history)
            step = AgentStep(iteration=iteration)

            # Try to parse a tool-call JSON block
            tool_called = False
            try:
                parsed = json.loads(raw_reply.strip())
                if isinstance(parsed, dict) and "action" in parsed:
                    tool_name = parsed["action"]
                    params    = parsed.get("params", {})
                    thought   = parsed.get("thought", "")

                    step.thought = thought

                    if tool_name not in TOOL_MAP:
                        logger.warning(f"Unknown tool requested: {tool_name}")
                        answer = f"I tried to call an unknown tool '{tool_name}'. Please rephrase."
                        break

                    tc = ToolCall(
                        id=str(uuid.uuid4()),
                        name=tool_name,
                        arguments=params,
                    )
                    step.tool_calls.append(tc)

                    logger.info(f"[{conversation_id}] Calling tool: {tool_name}({params})")
                    tool_result = TOOL_MAP[tool_name](**params)
                    step.tool_results.append({"tool": tool_name, "result": tool_result})

                    # Feed result back into history
                    history.append({"role": "assistant", "content": raw_reply})
                    history.append({
                        "role": "user",
                        "content": (
                            f"Tool '{tool_name}' returned:\n"
                            f"{json.dumps(tool_result, default=str)}\n\n"
                            "Now give a concise, helpful answer to the user based on this data."
                        ),
                    })

                    tool_called = True

            except (json.JSONDecodeError, TypeError):
                # LLM replied in plain text — no tool call needed
                pass

            steps.append(step)

            if not tool_called:
                # LLM gave a plain-text answer — we're done
                answer = raw_reply
                history.append({"role": "assistant", "content": answer})
                break

        else:
            # Hit max iterations without a plain-text answer
            answer = "I've reached the maximum number of tool calls. Please try a more specific question."
            logger.warning(f"[{conversation_id}] Max iterations ({self.max_iterations}) reached.")

        # Persist trimmed history
        _sessions[conversation_id] = history

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "namespace": namespace,
            "steps": steps,
            "model": self.llm.model,
            "provider": "ollama",
        }
