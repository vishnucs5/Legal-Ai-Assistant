from __future__ import annotations

from config.settings import settings


class AnthropicClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.default_model
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicClient.")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise RuntimeError("Install anthropic to use AnthropicClient.") from exc
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def complete(self, prompt: str, response_format: str = "json") -> str:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in message.content if getattr(block, "type", "") == "text")

