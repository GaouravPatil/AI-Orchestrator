import httpx


class OllamaService:
    """
    Thin wrapper around the Ollama REST API.
    Assumes Ollama is running at localhost:11434 (default).
    """

    BASE_URL = "http://localhost:11434"

    def __init__(self, model: str = "llama3"):
        self.model = model

    def chat(self, messages: list[dict]) -> str:
        """
        Send a list of messages to Ollama and return the assistant reply.

        messages format:
            [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        response = httpx.post(
            f"{self.BASE_URL}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def generate(self, prompt: str) -> str:
        """Single-turn text generation."""
        response = httpx.post(
            f"{self.BASE_URL}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["response"]
