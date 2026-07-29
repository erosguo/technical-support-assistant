import asyncio
from httpx import AsyncClient


class TestTicketAPI:
    def test_create_ticket(self, client: AsyncClient):
        async def run():
            resp = await client.post(
                "/api/v1/tickets",
                json={
                    "title": "服务器宕机",
                    "description": "生产环境无响应",
                    "priority": "critical",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "id" in data
            assert data["title"] == "服务器宕机"
            assert data["status"] == "open"

        asyncio.run(run())

    def test_list_tickets(self, client: AsyncClient):
        async def run():
            await client.post(
                "/api/v1/tickets",
                json={"title": "工单1", "description": "d1"},
            )
            await client.post(
                "/api/v1/tickets",
                json={"title": "工单2", "description": "d2"},
            )
            resp = await client.get("/api/v1/tickets")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 2

        asyncio.run(run())

    def test_get_ticket(self, client: AsyncClient):
        async def run():
            create_resp = await client.post(
                "/api/v1/tickets",
                json={"title": "查询测试", "description": "test"},
            )
            ticket_id = create_resp.json()["id"]
            resp = await client.get(f"/api/v1/tickets/{ticket_id}")
            assert resp.status_code == 200
            assert resp.json()["title"] == "查询测试"

        asyncio.run(run())

    def test_get_ticket_not_found(self, client: AsyncClient):
        async def run():
            resp = await client.get("/api/v1/tickets/nonexistent")
            assert resp.status_code == 404

        asyncio.run(run())

    def test_update_ticket_status(self, client: AsyncClient):
        async def run():
            create_resp = await client.post(
                "/api/v1/tickets",
                json={"title": "更新测试", "description": "d"},
            )
            ticket_id = create_resp.json()["id"]
            resp = await client.patch(
                f"/api/v1/tickets/{ticket_id}",
                json={"status": "in_progress"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "in_progress"

        asyncio.run(run())

    def test_delete_ticket(self, client: AsyncClient):
        async def run():
            create_resp = await client.post(
                "/api/v1/tickets",
                json={"title": "删除测试", "description": "d"},
            )
            ticket_id = create_resp.json()["id"]
            resp = await client.delete(f"/api/v1/tickets/{ticket_id}")
            assert resp.status_code == 200
            get_resp = await client.get(f"/api/v1/tickets/{ticket_id}")
            assert get_resp.status_code == 404

        asyncio.run(run())

    def test_create_ticket_missing_title(self, client: AsyncClient):
        async def run():
            resp = await client.post(
                "/api/v1/tickets",
                json={"description": "no title"},
            )
            assert resp.status_code == 422

        asyncio.run(run())
