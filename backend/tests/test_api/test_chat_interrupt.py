import asyncio
import json
from unittest.mock import patch
from httpx import AsyncClient
from app.models.error_pattern import ErrorPattern
from app.models.ticket import Ticket
from tests.mock_providers import MockLLMProvider


def _mock():
    return MockLLMProvider(
        responses={
            "分析用户问题的意图": "diagnosis",
            "default": "错误需要升级处理，请人工确认。",
        }
    )


class TestChatInterrupt:
    def test_chat_emits_interrupt_for_critical(
        self, client: AsyncClient, db_session, mock_llm
    ):
        ep = ErrorPattern(pattern="CRIT_ERR", severity="critical", solution="紧急修复")
        db_session.add(ep)
        db_session.commit()
        mock = _mock()

        async def run():
            with (
                patch("app.api.v1.chat.LLMRouter", return_value=mock),
                patch("app.agents.supervisor.LLMRouter", return_value=mock),
            ):
                resp = await client.post(
                    "/api/v1/chat/completions",
                    json={"content": "出现 CRIT_ERR 错误"},
                )
            assert resp.status_code == 200
            body = resp.text
            assert "interrupt" in body
            payload = json.loads(
                [line for line in body.splitlines() if line.startswith("data: ")][0][6:]
            )
            assert payload["interrupt"]["type"] == "escalation_approval"
            assert "question" in payload["interrupt"]

        asyncio.run(run())

    def test_approve_creates_ticket(self, client: AsyncClient, db_session):
        ep = ErrorPattern(pattern="SEVERE", severity="high", solution="排查日志")
        db_session.add(ep)
        db_session.commit()
        mock = _mock()

        async def run():
            with (
                patch("app.api.v1.chat.LLMRouter", return_value=mock),
                patch("app.agents.supervisor.LLMRouter", return_value=mock),
            ):
                resp = await client.post(
                    "/api/v1/chat/completions",
                    json={"content": "出现 SEVERE 错误"},
                )
                assert resp.status_code == 200
                conv_id = json.loads(
                    [
                        line
                        for line in resp.text.splitlines()
                        if line.startswith("data: ")
                    ][0][6:]
                )["conversation_id"]

                resume = await client.post(
                    "/api/v1/chat/completions/resume",
                    json={"conversation_id": conv_id, "approved": True},
                )
            assert resume.status_code == 200
            body = resume.text
            assert "[DONE]" in body

        asyncio.run(run())
        tickets = db_session.query(Ticket).all()
        assert len(tickets) >= 1

    def test_reject_no_ticket(self, client: AsyncClient, db_session):
        ep = ErrorPattern(pattern="MED", severity="medium", solution="检查配置")
        db_session.add(ep)
        db_session.commit()
        mock = _mock()

        async def run():
            with (
                patch("app.api.v1.chat.LLMRouter", return_value=mock),
                patch("app.agents.supervisor.LLMRouter", return_value=mock),
            ):
                resp = await client.post(
                    "/api/v1/chat/completions",
                    json={"content": "出现 MED 错误"},
                )
                assert resp.status_code == 200
                conv_id = json.loads(
                    [
                        line
                        for line in resp.text.splitlines()
                        if line.startswith("data: ")
                    ][0][6:]
                )["conversation_id"]

                resume = await client.post(
                    "/api/v1/chat/completions/resume",
                    json={"conversation_id": conv_id, "approved": False},
                )
            assert resume.status_code == 200

        asyncio.run(run())
        tickets = db_session.query(Ticket).all()
        assert len(tickets) == 0
