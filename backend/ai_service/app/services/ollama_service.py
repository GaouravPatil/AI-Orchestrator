"""
Thin wrapper around the Ollama /api/chat endpoint.
Reads base URL, model, and timeout from ai-service config.
"""
import httpx

from ai_service.app.core.config import settings
from ai_service.app.core.logger import logger


class OllamaService:

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

    def chat(self, messages: list[dict]) -> str:
        """
        Send a conversation history to Ollama and return the assistant reply text.

        messages format:
            [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        logger.debug(f"OllamaService.chat — model={self.model}, messages={len(messages)}")

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            logger.debug(f"OllamaService reply: {content[:120]}...")
            return content

        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.base_url}. "
                "Make sure `ollama serve` is running."
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama returned HTTP {e.response.status_code}: {e.response.text}")

    def generate(self, prompt: str) -> str:
        """Single-turn text generation via /api/generate."""
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()["response"]
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot reach Ollama at {self.base_url}.")
