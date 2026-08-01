"""Tests for F23: Multi-Model Fallback (FallbackLLMRouter)."""

import asyncio

import pytest

from app.services.llm_fallback import FallbackLLMRouter


class SuccessProvider:
    """Provider that always succeeds with a fixed reply/vector."""

    def __init__(self, reply: str = "ok", vector: list[float] | None = None):
        self.reply = reply
        self.vector = vector if vector is not None else [0.1, 0.2]

    async def chat(self, messages: list[dict], **kwargs) -> str:
        return self.reply

    async def embed(self, text: str) -> list[float]:
        return self.vector


class FailingProvider:
    """Provider that always raises."""

    def __init__(self, error: str = "boom"):
        self.error = error

    async def chat(self, messages: list[dict], **kwargs) -> str:
        raise RuntimeError(self.error)

    async def embed(self, text: str) -> list[float]:
        raise RuntimeError(self.error)


class TestFallbackLLMRouter:
    def test_chat_first_provider_succeeds(self):
        router = FallbackLLMRouter(
            [SuccessProvider("hello"), SuccessProvider("backup")]
        )
        reply = asyncio.run(router.chat([{"role": "user", "content": "hi"}]))
        assert reply == "hello"
        assert router.failures == []

    def test_chat_fallback_to_second(self):
        router = FallbackLLMRouter(
            [FailingProvider("fail1"), SuccessProvider("hello2")]
        )
        reply = asyncio.run(router.chat([{"role": "user", "content": "hi"}]))
        assert reply == "hello2"
        assert len(router.failures) == 1
        assert router.failures[0][0] == 0
        assert isinstance(router.failures[0][1], Exception)

    def test_chat_all_fail_raises(self):
        router = FallbackLLMRouter([FailingProvider("a"), FailingProvider("b")])
        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            asyncio.run(router.chat([{"role": "user", "content": "hi"}]))

    def test_chat_records_failures(self):
        router = FallbackLLMRouter(
            [FailingProvider("err1"), FailingProvider("err2"), SuccessProvider("ok")]
        )
        reply = asyncio.run(router.chat([{"role": "user", "content": "hi"}]))
        assert reply == "ok"
        assert len(router.failures) == 2
        assert router.failures[0][0] == 0
        assert router.failures[1][0] == 1
        assert isinstance(router.failures[0][1], RuntimeError)
        assert isinstance(router.failures[1][1], RuntimeError)

    def test_embed_fallback(self):
        router = FallbackLLMRouter(
            [FailingProvider(), SuccessProvider(vector=[1.0, 2.0, 3.0])]
        )
        vec = asyncio.run(router.embed("text"))
        assert vec == [1.0, 2.0, 3.0]
        assert len(router.failures) == 1
        assert router.failures[0][0] == 0
