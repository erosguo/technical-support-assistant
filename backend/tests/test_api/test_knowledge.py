import asyncio
from unittest.mock import patch
from httpx import AsyncClient
from app.models.knowledge import DocumentChunk


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

    def test_search_endpoint_with_citations(
        self, client: AsyncClient, db_session, mock_llm
    ):
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

            with (
                patch("app.api.v1.knowledge.LLMRouter", return_value=mock_llm),
                patch("app.api.v1.knowledge.settings.llm_api_key", "test-key"),
            ):
                resp = await client.post(
                    "/api/v1/knowledge/search",
                    params={"query": "SSL配置", "top_k": 5},
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "results" in data
            if data["results"]:
                result = data["results"][0]
                assert "document_title" in result
                assert "content" in result
                assert "score" in result

        asyncio.run(run())
