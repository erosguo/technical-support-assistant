import asyncio
import pytest
from app.services.llm import LLMRouter
from tests.mock_providers import MockLLMProvider


@pytest.fixture
def mock_provider():
    return MockLLMProvider(responses={"test": "hello world"})


class TestLLMRouter:
    def test_chat_returns_string(self, mock_provider):
        router = LLMRouter(provider=mock_provider)
        reply = asyncio.run(router.chat([{"role": "user", "content": "test"}]))
        assert isinstance(reply, str)
        assert reply == "hello world"

    def test_chat_stream_yields_chunks(self, mock_provider):
        router = LLMRouter(provider=mock_provider)

        async def run():
            chunks = []
            async for chunk in router.chat_stream(
                [{"role": "user", "content": "test"}]
            ):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(run())
        assert len(chunks) > 0
        assert "".join(chunks) == "hello world"

    def test_embed_returns_float_list(self, mock_provider):
        router = LLMRouter(provider=mock_provider)
        vector = asyncio.run(router.embed("test text"))
        assert isinstance(vector, list)
        assert all(isinstance(v, float) for v in vector)

    def test_embed_batch_returns_matching_count(self, mock_provider):
        router = LLMRouter(provider=mock_provider)
        vectors = asyncio.run(router.embed_batch(["a", "b", "c"]))
        assert len(vectors) == 3
