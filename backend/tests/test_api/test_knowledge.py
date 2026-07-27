import asyncio
from httpx import AsyncClient


class TestKnowledgeAPI:
    def test_upload_document(self, client: AsyncClient):
        async def run():
            resp = await client.post(
                "/api/v1/knowledge/documents",
                data={"title": "测试文档"},
                files={"file": ("test.md", b"# Hello World", "text/markdown")},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "id" in data
            assert data["title"] == "测试文档"

        asyncio.run(run())

    def test_list_documents(self, client: AsyncClient):
        async def run():
            await client.post(
                "/api/v1/knowledge/documents",
                data={"title": "Doc1"},
                files={"file": ("a.md", b"content a", "text/markdown")},
            )
            await client.post(
                "/api/v1/knowledge/documents",
                data={"title": "Doc2"},
                files={"file": ("b.md", b"content b", "text/markdown")},
            )
            resp = await client.get("/api/v1/knowledge/documents")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 2

        asyncio.run(run())

    def test_get_document(self, client: AsyncClient):
        async def run():
            create_resp = await client.post(
                "/api/v1/knowledge/documents",
                data={"title": "GetTest"},
                files={"file": ("g.md", b"# Get content", "text/markdown")},
            )
            doc_id = create_resp.json()["id"]
            resp = await client.get(f"/api/v1/knowledge/documents/{doc_id}")
            assert resp.status_code == 200
            assert resp.json()["title"] == "GetTest"

        asyncio.run(run())

    def test_delete_document(self, client: AsyncClient):
        async def run():
            create_resp = await client.post(
                "/api/v1/knowledge/documents",
                data={"title": "DelTest"},
                files={"file": ("d.md", b"delete me", "text/markdown")},
            )
            doc_id = create_resp.json()["id"]
            resp = await client.delete(f"/api/v1/knowledge/documents/{doc_id}")
            assert resp.status_code == 200
            get_resp = await client.get(f"/api/v1/knowledge/documents/{doc_id}")
            assert get_resp.status_code == 404

        asyncio.run(run())
