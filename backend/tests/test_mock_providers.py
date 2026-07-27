import asyncio
import pytest
from tests.mock_providers import MockLLMProvider


@pytest.fixture
def mock_llm():
    return MockLLMProvider(
        responses={
            "你好": "你好！我是技术支持助手，有什么可以帮助你的？",
            "default": "这是一个模拟回复，用于测试场景。",
        }
    )


class TestMockLLMProvider:
    def test_chat_returns_mock_response(self, mock_llm):
        reply = asyncio.run(mock_llm.chat([{"role": "user", "content": "你好"}]))
        assert "技术支持助手" in reply

    def test_chat_default_fallback(self, mock_llm):
        reply = asyncio.run(mock_llm.chat([{"role": "user", "content": "未知问题"}]))
        assert reply == "这是一个模拟回复，用于测试场景。"

    def test_call_history_tracked(self, mock_llm):
        asyncio.run(mock_llm.chat([{"role": "user", "content": "你好"}]))
        assert len(mock_llm.call_history) == 1
        assert mock_llm.call_history[0]["messages"][-1]["content"] == "你好"

    def test_chat_stream_yields_chunks(self, mock_llm):
        async def run():
            chunks = []
            async for chunk in mock_llm.chat_stream(
                [{"role": "user", "content": "你好"}]
            ):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(run())
        assert len(chunks) > 0
        assert "".join(chunks) == "你好！我是技术支持助手，有什么可以帮助你的？"

    def test_embed_returns_float_list(self, mock_llm):
        vector = asyncio.run(mock_llm.embed("test text"))
        assert isinstance(vector, list)
        assert all(isinstance(v, float) for v in vector)
        assert len(vector) == 3

    def test_embed_batch_returns_matching_count(self, mock_llm):
        vectors = asyncio.run(mock_llm.embed_batch(["a", "b", "c"]))
        assert len(vectors) == 3
