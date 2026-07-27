"""测试替身：所有外部依赖的 Mock 实现"""


class MockLLMProvider:
    def __init__(self, responses: dict[str, str] = None):
        self.responses = responses or {}
        self.call_history: list[dict] = []

    async def chat(self, messages: list[dict], **kwargs) -> str:
        self.call_history.append({"messages": messages, "kwargs": kwargs})
        query = messages[-1]["content"] if messages else ""
        for pattern, reply in self.responses.items():
            if pattern in query:
                return reply
        return self.responses.get("default", "Mock reply")

    async def chat_stream(self, messages: list[dict], **kwargs):
        reply = await self.chat(messages, **kwargs)
        for char in reply:
            yield char

    async def embed(self, text: str) -> list[float]:
        return [0.1] * 3

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class MockEmbeddingProvider:
    dimension: int = 3

    async def embed(self, text: str) -> list[float]:
        return [0.1] * self.dimension

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]
