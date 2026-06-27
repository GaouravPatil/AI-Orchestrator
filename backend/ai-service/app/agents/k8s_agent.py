import json
import uuid

from ai_service.app.services.ollama_service import OllamaService
from ai_service.app.tools import k8s_tools

SYSTEM_PROMPT = """You are an AI DevOps assistant for a Kubernetes cluster.
You can answer questions about the cluster and perform operations by calling tools.

When you need to take an action, respond with a JSON block in this exact format:
{
  "thought": "why you are taking this action",
  "action": "tool_name",
  "params": { ... }
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

If you don't need to take an action, respond naturally in plain text.
Always be concise and helpful.
"""

TOOL_MAP = {
    "list_namespaces": k8s_tools.list_namespaces,
    "list_nodes": k8s_tools.list_nodes,
    "list_pods": k8s_tools.list_pods,
    "list_deployments": k8s_tools.list_deployments,
    "list_services": k8s_tools.list_services,
    "list_events": k8s_tools.list_events,
    "get_pod_logs": k8s_tools.get_pod_logs,
    "create_deployment": k8s_tools.create_deployment,
    "scale_deployment": k8s_tools.scale_deployment,
    "delete_deployment": k8s_tools.delete_deployment,
}

# In-memory session store (replace with Redis/DB in production)
_sessions: dict[str, list[dict]] = {}


class K8sAgent:

    def __init__(self):
        self.llm = OllamaService()

    def chat(self, message: str, session_id: str | None = None) -> dict:

        if session_id is None:
            session_id = str(uuid.uuid4())

        # Build conversation history
        if session_id not in _sessions:
            _sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

        history = _sessions[session_id]
        history.append({"role": "user", "content": message})

        # Ask the LLM
        raw_reply = self.llm.chat(history)

        action_taken = None

        # Check if LLM wants to call a tool
        try:
            parsed = json.loads(raw_reply.strip())
            if isinstance(parsed, dict) and "action" in parsed:
                tool_name = parsed["action"]
                params = parsed.get("params", {})

                if tool_name in TOOL_MAP:
                    tool_result = TOOL_MAP[tool_name](**params)
                    action_taken = tool_name

                    # Feed tool result back to LLM for a final natural language reply
                    history.append({"role": "assistant", "content": raw_reply})
                    history.append({
                        "role": "user",
                        "content": f"Tool result: {json.dumps(tool_result, default=str)}\n\nNow summarize this for the user.",
                    })
                    raw_reply = self.llm.chat(history)

        except (json.JSONDecodeError, TypeError):
            # LLM replied in plain text — no tool call needed
            pass

        history.append({"role": "assistant", "content": raw_reply})
        _sessions[session_id] = history

        return {
            "reply": raw_reply,
            "session_id": session_id,
            "action_taken": action_taken,
        }
