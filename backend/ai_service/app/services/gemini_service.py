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
        self.timeout = timeout or settings.GEMINI_TIMEOUT
        self.temperature = temperature or settings.AGENT_TEMPERATURE

        # Resolve provider and model from model name if prefix exists
        # e.g., "openrouter/qwen/qwen-2.5-coder-32b:free" -> provider="openrouter", model="qwen/qwen-2.5-coder-32b:free"
        raw_model = model or settings.GEMINI_MODEL or "gemini-2.0-flash"
        provider_from_model = None
        resolved_model = raw_model

        if isinstance(raw_model, str) and "/" in raw_model:
            parts = raw_model.split("/", 1)
            possible_provider = parts[0].lower()
            if possible_provider in ("google", "gemini", "openrouter", "ollama", "openai"):
                provider_from_model = possible_provider
                resolved_model = parts[1]

        self.provider = provider_from_model or settings.LLM_PROVIDER.lower()
        
        # If openrouter provider was specified as a prefix, and the rest doesn't contain a slash,
        # it means the model is something like "openrouter/free", so the actual model slug must be "openrouter/free"
        if self.provider == "openrouter" and provider_from_model == "openrouter" and "/" not in resolved_model:
            resolved_model = f"openrouter/{resolved_model}"

        self.model = resolved_model

        # Determine connection parameters based on provider
        if self.provider == "ollama":
            self.base_url = base_url or settings.LLM_BASE_URL or "http://localhost:11434/v1"
            self.api_key = api_key or settings.LLM_API_KEY or "ollama"
        elif self.provider in ("gemini", "google"):
            self.provider = "gemini"  # normalize
            self.base_url = base_url or settings.GEMINI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/"
            self.api_key = api_key or settings.GOOGLE_API_KEY
        elif self.provider == "openrouter":
            self.base_url = base_url or settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
            self.api_key = api_key or settings.OPENROUTER_API_KEY
        else:
            # Generic OpenAI-compatible
            self.provider = "openai"
            self.base_url = base_url or settings.LLM_BASE_URL
            self.api_key = api_key or settings.LLM_API_KEY

        if not self.api_key and self.provider != "ollama":
            logger.warning(f"API key for provider '{self.provider}' is empty. Requests may fail if authorization is required.")

        logger.info(f"Initializing LLM Service (Provider: {self.provider}, Model: {self.model}, Base URL: {self.base_url})")

        # OpenRouter suggests specific headers
        default_headers = {}
        if self.provider == "openrouter":
            default_headers = {
                "HTTP-Referer": "https://github.com/google-deepmind/ai-orchestrator",
                "X-Title": "AI DevOps Orchestrator",
            }

        self._client = OpenAI(
            api_key=self.api_key or "placeholder_key",
            base_url=self.base_url.rstrip("/"),
            timeout=self.timeout,
            default_headers=default_headers if default_headers else None,
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
