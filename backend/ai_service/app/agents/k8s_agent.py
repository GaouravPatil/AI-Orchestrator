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
from ai_service.app.services.gemini_service import GeminiService
from ai_service.app.tools import k8s_tools

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an AI DevOps assistant for a live Kubernetes cluster.
Your job is to answer user questions by calling the appropriate tool — NEVER guess or invent data.

RULES (follow strictly):
1. When the user asks for cluster information (nodes, pods, deployments, etc.), you MUST call the relevant tool first.
2. To call a tool, output ONLY a raw JSON object (no markdown, no backticks, no extra text):
   {"thought": "<why you are calling this tool>", "action": "<tool_name>", "params": {<key: value>}}
3. Do NOT include any text before or after the JSON.
4. NEVER make up or hallucinate Kubernetes resource names, statuses, or counts.
5. Only after receiving real tool results should you compose a plain-text answer.
6. If no tool is needed (e.g. a general question), respond in plain text only.

Available tools:
- list_namespaces()                                         → list all namespaces
- list_nodes()                                              → list all cluster nodes
- list_pods()                                               → list all pods across namespaces
- list_deployments()                                        → list all deployments
- list_services(namespace)                                  → list services in a namespace
- list_events(namespace)                                    → list recent events in a namespace
- get_pod_logs(namespace, pod_name, tail=50)                → get pod logs
- create_deployment(name, image, replicas, namespace, port) → create a deployment
- scale_deployment(name, replicas, namespace)               → scale a deployment
- delete_deployment(name, namespace)                        → delete a deployment
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
        self.router_llm = GeminiService(model=settings.MODEL_ROUTER)
        self.fast_llm = GeminiService(model=settings.MODEL_FAST)
        self.complex_llm = GeminiService(model=settings.MODEL_COMPLEX)
        # Keep self.llm referencing fast_llm for health check API compatibility
        self.llm = self.fast_llm
        self.max_iterations = settings.MAX_TOOL_ITERATIONS

    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        namespace: str = "default",
        bearer_token: Optional[str] = None,
    ) -> dict:
        """
        Run the bifurcated agentic loop for a user message.
        """
        # ── Setup ──────────────────────────────────────────────────────────
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        if bearer_token:
            k8s_tools.set_token(bearer_token)

        if conversation_id not in _sessions:
            _sessions[conversation_id] = []

        global_history = _sessions[conversation_id]

        # ── Step 1: Bifurcation / Routing Phase ─────────────────────────────
        logger.info(f"[{conversation_id}] Router analyzing query: '{message}'")
        
        # Build prompt for router
        router_prompt = f"""
Analyze the user's latest message and determine if it contains multiple independent requests or tasks.
If it does, split it into distinct, self-contained sub-queries.
Also, classify each query/sub-query into one of these categories:
- READ_ONLY: Querying/reading cluster state (e.g., list pods, check node status, show deployments, inspect services).
- ADMIN: Mutating/changing cluster state (e.g., scale replica count, create deployments, delete resources).
- DIAGNOSTIC: Investigating failures (e.g., check pod logs, fetch namespace events, analyze crashloops).
- GENERAL: General chat, greetings, casual talk, or general non-k8s questions.

Output your response strictly as a raw JSON object (no markdown, no backticks, no extra text):
{{
  "is_multipart": true,
  "tasks": [
    {{"query": "Self-contained sub-query 1", "category": "READ_ONLY/ADMIN/DIAGNOSTIC/GENERAL"}},
    {{"query": "Self-contained sub-query 2", "category": "READ_ONLY/ADMIN/DIAGNOSTIC/GENERAL"}}
  ]
}}

User query: "{message}"
"""
        
        try:
            raw_router_reply = self.router_llm.generate(router_prompt)
            cleaned = raw_router_reply.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0]
                cleaned = cleaned.strip()
            if not cleaned.startswith("{"):
                import re
                json_match = re.search(r'\{[\s\S]*"tasks"[\s\S]*\}', cleaned)
                if json_match:
                    cleaned = json_match.group(0)

            router_data = json.loads(cleaned)
            is_multipart = router_data.get("is_multipart", False)
            tasks = router_data.get("tasks", [])
            if not tasks:
                tasks = [{"query": message, "category": "READ_ONLY"}]
        except Exception as e:
            logger.warning(f"[{conversation_id}] Router parsing failed: {e}. Falling back to single task.")
            is_multipart = False
            # Fallback heuristic
            lower_msg = message.lower()
            category = "READ_ONLY"
            if any(kw in lower_msg for kw in ["scale", "delete", "create", "deploy"]):
                category = "ADMIN"
            elif any(kw in lower_msg for kw in ["why", "failed", "crash", "error", "logs"]):
                category = "DIAGNOSTIC"
            tasks = [{"query": message, "category": category}]

        logger.info(f"[{conversation_id}] Bifurcation result: multipart={is_multipart}, tasks={tasks}")

        # ── Step 2: Execution Phase ──────────────────────────────────────────
        all_steps = []
        sub_answers = []

        # Create step 0 detailing routing decisions (highly visual trace)
        routing_desc = f"🔍 Query Router classified input. Multipart={is_multipart}\n"
        for idx, t in enumerate(tasks, 1):
            target_model = settings.MODEL_FAST if t["category"] in ("READ_ONLY", "GENERAL") else settings.MODEL_COMPLEX
            routing_desc += f"  ↳ Task {idx}: '{t['query']}' [{t['category']}] routed to {target_model}\n"

        all_steps.append(AgentStep(
            iteration=0,
            thought=routing_desc.strip(),
            tool_calls=[],
            tool_results=[]
        ))

        for idx, task in enumerate(tasks, 1):
            sub_query = task["query"]
            category = task["category"]
            
            logger.info(f"[{conversation_id}] Executing sub-task {idx}/{len(tasks)}: '{sub_query}' [{category}]")
            sub_answer, sub_steps = self._run_sub_agent(
                query=sub_query,
                category=category,
                history_context=global_history,
                namespace=namespace,
            )
            sub_answers.append(sub_answer)
            # Offset iteration count for sub-steps to display sequentially in UI trace
            for s in sub_steps:
                s.iteration = len(all_steps)
                all_steps.append(s)

        # ── Step 3: Synthesis Phase ──────────────────────────────────────────
        if is_multipart and len(tasks) > 1:
            logger.info(f"[{conversation_id}] Consolidating answers for multi-part query...")
            synthesis_prompt = f"""
You are a consolidator for a Kubernetes cluster management assistant.
Your job is to combine the results of multiple sub-queries into a single, cohesive, professional response.
Make sure the response addresses all parts of the user's original query.
Do not mention that you are a consolidator or that the query was split. Simply present the final merged answer.

User original query: "{message}"

Sub-task results:
"""
            for t, ans in zip(tasks, sub_answers):
                synthesis_prompt += f"\n- Sub-task: {t['query']}\n  Result: {ans}\n"

            try:
                final_answer = self.fast_llm.generate(synthesis_prompt)
            except Exception as e:
                logger.error(f"[{conversation_id}] Synthesis failed: {e}")
                final_answer = "\n\n".join([f"**Part {idx} ({t['query']}):**\n{ans}" for idx, (t, ans) in enumerate(zip(tasks, sub_answers), 1)])
        else:
            final_answer = sub_answers[0] if sub_answers else "No result generated."

        # ── Step 4: Persist Clean Global History ─────────────────────────────
        # Only store the original user question and final synthesized response in the history.
        # This completely avoids polluting context window with intermediate tool JSONs!
        global_history.append({"role": "user", "content": message})
        global_history.append({"role": "assistant", "content": final_answer})

        # Trim global history to stay within rolling window
        max_msgs = settings.MAX_HISTORY_MESSAGES
        if len(global_history) > max_msgs:
            global_history = global_history[-max_msgs:]

        _sessions[conversation_id] = global_history

        # Determine which models and providers responded
        invoked_models = []
        invoked_providers = []

        if is_multipart and len(tasks) > 1:
            invoked_models.append(f"router:{self.router_llm.model}")
            invoked_providers.append(self.router_llm.provider)

        for task in tasks:
            cat = task["category"]
            if cat == "GENERAL":
                # General chats only run fast LLM and don't call tools
                model_lbl = f"fast:{self.fast_llm.model}"
                prov_lbl = self.fast_llm.provider
            elif cat == "READ_ONLY":
                model_lbl = f"fast:{self.fast_llm.model}"
                prov_lbl = self.fast_llm.provider
            else:
                model_lbl = f"complex:{self.complex_llm.model}"
                prov_lbl = self.complex_llm.provider

            if model_lbl not in invoked_models:
                invoked_models.append(model_lbl)
            if prov_lbl not in invoked_providers:
                invoked_providers.append(prov_lbl)

        used_model = " + ".join(invoked_models)
        used_provider = " / ".join(invoked_providers)

        return {
            "conversation_id": conversation_id,
            "answer": final_answer,
            "namespace": namespace,
            "steps": all_steps,
            "model": used_model,
            "provider": used_provider,
        }

    def _run_sub_agent(
        self,
        query: str,
        category: str,
        history_context: list[dict],
        namespace: str,
    ) -> tuple[str, list[AgentStep]]:
        """
        Run a single sub-agent execution loop.
        """
        # General chat: bypass tool agent loop entirely to save tokens and time
        if category == "GENERAL":
            messages = [
                {"role": "system", "content": "You are a helpful, professional DevOps assistant. Keep your response brief and friendly."}
            ]
            # Copy recent history (only user/assistant roles, ignoring system/tool details)
            for msg in history_context[-4:]:
                if msg["role"] in ("user", "assistant"):
                    messages.append(msg)
            messages.append({"role": "user", "content": query})
            
            try:
                reply = self.fast_llm.chat(messages)
                return reply, []
            except Exception as e:
                logger.error(f"Failed general sub-agent chat: {e}")
                return f"I encountered an error replying to your request: {e}", []

        # Read-only uses fast model; Admin/Diagnostics use complex model
        llm = self.fast_llm if category == "READ_ONLY" else self.complex_llm
        model_name = llm.model

        # Build clean temporary history context
        temp_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history_context:
            if msg["role"] in ("user", "assistant"):
                temp_history.append(msg)

        temp_history.append({"role": "user", "content": query})

        steps: list[AgentStep] = []
        answer = ""

        for iteration in range(1, self.max_iterations + 1):
            raw_reply = llm.chat(temp_history)
            step = AgentStep(iteration=iteration)

            # JSON extraction and clean up
            cleaned = raw_reply.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0]
                cleaned = cleaned.strip()
            if not cleaned.startswith("{"):
                import re
                json_match = re.search(r'\{[\s\S]*"action"[\s\S]*\}', cleaned)
                if json_match:
                    cleaned = json_match.group(0)

            tool_called = False
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "action" in parsed:
                    tool_name = parsed["action"]
                    params = parsed.get("params", {})
                    thought = parsed.get("thought", "")

                    step.thought = thought

                    if tool_name not in TOOL_MAP:
                        logger.warning(f"Unknown tool: {tool_name}")
                        answer = f"I tried to call an unknown tool '{tool_name}'."
                        break

                    tc = ToolCall(
                        id=str(uuid.uuid4()),
                        name=tool_name,
                        arguments=params,
                    )
                    step.tool_calls.append(tc)

                    logger.info(f"Sub-agent calling tool: {tool_name}({params})")
                    tool_result = TOOL_MAP[tool_name](**params)
                    step.tool_results.append({"tool": tool_name, "result": tool_result})

                    # Feed tool output back to sub-agent context
                    temp_history.append({"role": "assistant", "content": raw_reply})
                    temp_history.append({
                        "role": "user",
                        "content": (
                            f"Tool '{tool_name}' returned:\n"
                            f"{json.dumps(tool_result, default=str)}\n\n"
                            "Now give a concise, helpful plain-text answer to the user based on this real data. "
                            "Do NOT output JSON."
                        ),
                    })
                    tool_called = True
            except (json.JSONDecodeError, TypeError):
                # Plain text reply, or tool skip handling
                if iteration == 1 and not tool_called:
                    tool_keywords = [
                        "node", "pod", "deployment", "namespace", "service",
                        "log", "scale", "delete", "create", "event", "cluster"
                    ]
                    needs_tool = any(kw in query.lower() for kw in tool_keywords)
                    if needs_tool:
                        logger.warning("Sub-agent skipped tool call on iteration 1 — forcing retry")
                        temp_history.append({"role": "assistant", "content": raw_reply})
                        temp_history.append({
                            "role": "user",
                            "content": (
                                "IMPORTANT: You must NOT guess or invent cluster data. "
                                "Call the appropriate tool first by outputting ONLY a raw JSON object: "
                                '{"thought": "<reason>", "action": "<tool_name>", "params": {}}'
                                " — no markdown, no extra text."
                            ),
                        })
                        steps.append(step)
                        continue

            steps.append(step)

            if not tool_called:
                answer = raw_reply
                break
        else:
            answer = "The sub-agent reached maximum tool iterations."

        return answer, steps
