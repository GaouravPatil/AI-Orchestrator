"""
Thin wrapper around Google Gemini API using the OpenAI-compatible client.
Reads base URL, model, and API key from ai-service config.

The Gemini API exposes an OpenAI-compatible endpoint — no extra SDK required.
Docs: https://ai.google.dev/gemini-api/docs/openai
Get your API key: https://aistudio.google.com/apikey
"""
from openai import OpenAI

from ai_service.app.core.config import settings
from ai_service.app.core.logger import logger


class GeminiService:

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        temperature: float | None = None,
    ):
        self.provider = settings.LLM_PROVIDER.lower()
        self.timeout = timeout or settings.GEMINI_TIMEOUT
        self.temperature = temperature or settings.AGENT_TEMPERATURE

        # Determine default model and connection parameters based on provider
        if self.provider == "ollama":
            self.model = model or settings.MODEL_FAST or "llama3"
            self.base_url = base_url or settings.LLM_BASE_URL or "http://localhost:11434/v1"
            self.api_key = api_key or settings.LLM_API_KEY or "ollama"
        elif self.provider == "gemini":
            self.model = model or settings.GEMINI_MODEL or "gemini-2.0-flash"
            self.base_url = base_url or settings.GEMINI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/"
            self.api_key = api_key or settings.GOOGLE_API_KEY
        else:
            # Generic OpenAI-compatible
            self.model = model or settings.GEMINI_MODEL
            self.base_url = base_url or settings.LLM_BASE_URL
            self.api_key = api_key or settings.LLM_API_KEY

        logger.info(f"Initializing LLM Service (Provider: {self.provider}, Model: {self.model}, Base URL: {self.base_url})")

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url.rstrip("/"),
            timeout=self.timeout,
        )

    def chat(self, messages: list[dict]) -> str:
        """
        Send a conversation history to the LLM and return the assistant reply text.
        """
        logger.debug(f"LLMService.chat — provider={self.provider}, model={self.model}, messages={len(messages)}")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            logger.debug(f"LLM reply: {content[:120]}...")
            return content

        except Exception as e:
            error_msg = str(e)
            provider_name = self.provider.upper()
            if "401" in error_msg or "API_KEY_INVALID" in error_msg or "authentication" in error_msg.lower():
                raise RuntimeError(
                    f"{provider_name} authentication failed. "
                    f"Check your API key settings in your .env file."
                )
            if "Connection" in error_msg or "connect" in error_msg.lower():
                raise RuntimeError(
                    f"Cannot reach {provider_name} API at {self.base_url}. "
                    f"Verify that your {provider_name} service is running and accessible."
                )
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise RuntimeError(
                    f"{provider_name} API quota exceeded or rate limited. Please check your usage limits."
                )
            raise RuntimeError(f"{provider_name} API error: {error_msg}")

    def generate(self, prompt: str) -> str:
        """Single-turn text generation convenience method."""
        return self.chat([{"role": "user", "content": prompt}])
