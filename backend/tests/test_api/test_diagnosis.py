import asyncio
from unittest.mock import patch
from httpx import AsyncClient
from app.models.error_pattern import ErrorPattern


class TestDiagnosisAPI:
    def _create_pattern(self, db_session):
        ep = ErrorPattern(pattern="ERR_", solution="请查阅错误手册", severity="high")
        db_session.add(ep)
        db_session.commit()
        return ep

    def test_diagnose_error_text(self, client: AsyncClient, db_session, mock_llm):
        async def run():
            self._create_pattern(db_session)
            with patch("app.api.v1.diagnosis.LLMRouter", return_value=mock_llm):
                resp = await client.post(
                    "/api/v1/diagnosis",
                    json={"error_text": "系统出现 ERR_500 错误"},
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "matches" in data
            assert len(data["matches"]) >= 1

        asyncio.run(run())

    def test_diagnose_no_match(self, client: AsyncClient, mock_llm):
        async def run():
            with patch("app.api.v1.diagnosis.LLMRouter", return_value=mock_llm):
                resp = await client.post(
                    "/api/v1/diagnosis",
                    json={"error_text": "未知错误信息"},
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert data["matches"] == []

        asyncio.run(run())

    def test_diagnose_with_conversation(
        self, client: AsyncClient, db_session, mock_llm
    ):
        async def run():
            conv_resp = await client.post(
                "/api/v1/chat/conversations", json={"title": "诊断测试"}
            )
            conv_id = conv_resp.json()["id"]
            self._create_pattern(db_session)
            with patch("app.api.v1.diagnosis.LLMRouter", return_value=mock_llm):
                resp = await client.post(
                    "/api/v1/diagnosis",
                    json={
                        "error_text": "ERR_500 连接失败",
                        "conversation_id": conv_id,
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "conversation_id" in data
            assert data["conversation_id"] == conv_id

        asyncio.run(run())

    def test_diagnose_missing_error_text(self, client: AsyncClient):
        async def run():
            resp = await client.post("/api/v1/diagnosis", json={})
            assert resp.status_code == 422

        asyncio.run(run())
