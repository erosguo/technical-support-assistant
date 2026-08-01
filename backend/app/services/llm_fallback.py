"""F23: Multi-Model Fallback.

Wraps multiple LLM providers in a chain so that if one provider fails the
router transparently falls back to the next. ``self.failures`` records the
(provider_index, exception) tuples from the most recent call for debugging.
"""

import logging

logger = logging.getLogger(__name__)


class FallbackLLMRouter:
    """Tries each provider in order, returning the first successful response."""

    def __init__(self, providers: list):
        self._providers = list(providers)
        self.failures: list[tuple[int, Exception]] = []

    async def chat(self, messages: list[dict], **kwargs) -> str:
        self.failures = []
        for index, provider in enumerate(self._providers):
            try:
                return await provider.chat(messages, **kwargs)
            except Exception as exc:  # noqa: BLE001 — fall through on any provider error
                self.failures.append((index, exc))
                logger.warning("LLM provider %d chat failed: %s", index, exc)
        raise RuntimeError("All LLM providers failed")

    async def embed(self, text: str) -> list[float]:
        self.failures = []
        for index, provider in enumerate(self._providers):
            try:
                return await provider.embed(text)
            except Exception as exc:  # noqa: BLE001 — fall through on any provider error
                self.failures.append((index, exc))
                logger.warning("LLM provider %d embed failed: %s", index, exc)
        raise RuntimeError("All LLM providers failed")
