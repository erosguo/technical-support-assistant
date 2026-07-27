import asyncio
import json
from unittest.mock import patch
from httpx import AsyncClient
from app.models.knowledge import DocumentChunk


class TestChatAPI:
    def test_health_check(self, client: AsyncClient):
        async def run():
            resp = await client.get("/api/v1/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"

        asyncio.run(run())

    def test_create_conversation(self, client: AsyncClient):
        async def run():
            resp = await client.post(
                "/api/v1/chat/conversations", json={"title": "测试"}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "id" in data
            assert data["title"] == "测试"

        asyncio.run(run())

    def test_list_conversations(self, client: AsyncClient):
        async def run():
            await client.post("/api/v1/chat/conversations", json={"title": "对话1"})
            await client.post("/api/v1/chat/conversations", json={"title": "对话2"})
            resp = await client.get("/api/v1/chat/conversations")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 2

        asyncio.run(run())

    def test_get_conversation_not_found(self, client: AsyncClient):
        async def run():
            resp = await client.get("/api/v1/chat/conversations/nonexistent")
            assert resp.status_code == 404

        asyncio.run(run())

    def test_chat_returns_citations_in_sse(
        self, client: AsyncClient, db_session, mock_llm
    ):
        """Upload a doc with embeddings, chat with knowledge, verify citations in SSE."""

        async def run():
            create_resp = await client.post(
                "/api/v1/knowledge/documents",
                data={"title": "SSL Guide"},
                files={
                    "file": (
                        "ssl.md",
                        b"CSR generation is the first step to configure SSL",
                        "text/markdown",
                    )
                },
            )
            doc_id = create_resp.json()["id"]
            chunk = DocumentChunk(
                document_id=doc_id,
                content="CSR generation is the first step to configure SSL",
                chunk_index=0,
                embedding=[0.1, 0.2, 0.3],
            )
            db_session.add(chunk)
            db_session.commit()

            conv_resp = await client.post(
                "/api/v1/chat/conversations", json={"title": "SSL测试"}
            )
            conv_id = conv_resp.json()["id"]

            with (
                patch("app.api.v1.chat.LLMRouter", return_value=mock_llm),
                patch("app.agents.supervisor.LLMRouter", return_value=mock_llm),
                patch("app.api.v1.chat.settings.llm_api_key", "test-key"),
            ):
                resp = await client.post(
                    "/api/v1/chat/completions",
                    json={"content": "如何配置SSL?", "conversation_id": conv_id},
                )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")

            lines = resp.text.strip().split("\n")
            events = []
            for line in lines:
                if line.startswith("data: "):
                    events.append(line[6:])

            assert len(events) >= 2
            first = json.loads(events[0])
            assert "content" in first
            assert first["conversation_id"] == conv_id
            last = events[-1]
            assert last == "[DONE]"

        asyncio.run(run())
