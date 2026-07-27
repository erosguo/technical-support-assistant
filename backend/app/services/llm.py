from typing import AsyncGenerator, Protocol


class LLMProvider(Protocol):
    """Protocol for LLM providers. Implement this to support backends."""

    async def chat(self, messages: list[dict], **kwargs) -> str: ...
    async def chat_stream(
        self, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]: ...
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIProvider:
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def chat(self, messages: list[dict], **kwargs) -> str:
        resp = await self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
        )
        return resp.choices[0].message.content or ""

    async def chat_stream(
        self, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        stream = await self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: str) -> list[float]:
        from app.core.config import settings

        resp = await self._client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return resp.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        from app.core.config import settings

        resp = await self._client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        return [d.embedding for d in resp.data]


class LLMRouter:
    def __init__(self, provider: LLMProvider = None):
        self._provider = provider

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            from app.core.config import settings

            self._provider = OpenAIProvider(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )
        return self._provider

    async def chat(self, messages: list[dict], **kwargs) -> str:
        return await self.provider.chat(messages, **kwargs)

    async def chat_stream(
        self, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.provider.chat_stream(messages, **kwargs):
            yield chunk

    async def embed(self, text: str) -> list[float]:
        return await self.provider.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return await self.provider.embed_batch(texts)
