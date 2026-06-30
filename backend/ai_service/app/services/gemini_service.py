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
        self.model = model or settings.GEMINI_MODEL
        self.timeout = timeout or settings.GEMINI_TIMEOUT
        self.temperature = temperature or settings.AGENT_TEMPERATURE

        self._client = OpenAI(
            api_key=api_key or settings.GOOGLE_API_KEY,
            # Google's OpenAI-compatible base URL
            base_url=(base_url or settings.GEMINI_BASE_URL).rstrip("/"),
            timeout=self.timeout,
        )

    def chat(self, messages: list[dict]) -> str:
        """
        Send a conversation history to Gemini and return the assistant reply text.

        messages format:
            [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        logger.debug(f"GeminiService.chat — model={self.model}, messages={len(messages)}")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            logger.debug(f"GeminiService reply: {content[:120]}...")
            return content

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "API_KEY_INVALID" in error_msg or "authentication" in error_msg.lower():
                raise RuntimeError(
                    "Gemini API authentication failed. "
                    "Check that GOOGLE_API_KEY is set correctly in ai_service/.env. "
                    "Get your key at: https://aistudio.google.com/apikey"
                )
            if "Connection" in error_msg or "connect" in error_msg.lower():
                raise RuntimeError(
                    f"Cannot reach Gemini API at {settings.GEMINI_BASE_URL}. "
                    "Check your internet connection."
                )
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise RuntimeError(
                    "Gemini API quota exceeded. Check your Google AI Studio usage limits."
                )
            raise RuntimeError(f"Gemini API error: {error_msg}")

    def generate(self, prompt: str) -> str:
        """Single-turn text generation convenience method."""
        return self.chat([{"role": "user", "content": prompt}])
