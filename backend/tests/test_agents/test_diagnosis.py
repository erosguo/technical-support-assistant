import asyncio
import pytest
from sqlalchemy.orm import Session
from app.agents.supervisor import build_supervisor_graph, AgentState
from app.models.error_pattern import ErrorPattern
from tests.mock_providers import MockLLMProvider


@pytest.fixture
def mock_provider():
    return MockLLMProvider(
        responses={
            "error_12345": "diagnosis",
            "hello": "general",
            "default": "这是一个诊断回复，建议检查系统配置。",
        }
    )


class TestDiagnosisAgent:
    def test_diagnosis_node_returns_reply(self, mock_provider, db_session: Session):
        ep = ErrorPattern(pattern="ERR_12345", solution="参考错误代码手册")
        db_session.add(ep)
        db_session.commit()

        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "出现 error_12345 错误"}],
            "user_intent": "diagnosis",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "ERR_12345",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert len(last_msg["content"]) > 0
        assert "diagnosis" in result.get("sub_agent_outputs", {})

    def test_diagnosis_node_no_match_fallback(self, mock_provider, db_session: Session):
        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "奇怪的错误发生"}],
            "user_intent": "diagnosis",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "UNKNOWN_ERROR_XYZ",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert len(last_msg["content"]) > 0

    def test_diagnosis_node_injects_matched_solutions(
        self, mock_provider, db_session: Session
    ):
        mock_provider.responses["超时"] = "diagnosis"
        ep = ErrorPattern(
            pattern="Timeout", solution="增加超时时间到30秒", severity="high"
        )
        db_session.add(ep)
        db_session.commit()

        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "连接超时"}],
            "user_intent": "diagnosis",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "Connection Timeout Error",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        diag = result.get("sub_agent_outputs", {}).get("diagnosis", {})
        assert len(diag.get("matches", [])) >= 1
        assert diag["matches"][0]["solution"] == "增加超时时间到30秒"
