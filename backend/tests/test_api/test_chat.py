import asyncio
from httpx import AsyncClient


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
