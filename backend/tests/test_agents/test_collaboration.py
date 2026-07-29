import asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from sqlalchemy.orm import Session
from app.agents.supervisor import build_supervisor_graph, AgentState
from app.models.error_pattern import ErrorPattern
from app.models.ticket import Ticket
from tests.mock_providers import MockLLMProvider


class TestMultiAgentWorkflow:
    def test_diagnosis_triggers_escalation(self, db_session: Session):
        ep = ErrorPattern(
            pattern="SEVERE_ERR", severity="critical", solution="紧急修复"
        )
        db_session.add(ep)
        db_session.commit()

        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "diagnosis",
                "default": "严重错误，需要升级处理。",
            }
        )
        checkpointer = MemorySaver()
        graph = build_supervisor_graph(
            llm=mock, session=db_session, checkpointer=checkpointer
        )
        state: AgentState = {
            "messages": [{"role": "user", "content": "出现 SEVERE_ERR 错误"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "SEVERE_ERR",
            "citations": [],
        }

        async def run():
            await graph.ainvoke(state, config={"configurable": {"thread_id": "col-1"}})
            result = await graph.ainvoke(
                Command(resume={"approved": True}),
                config={"configurable": {"thread_id": "col-1"}},
            )
            return result

        result = asyncio.run(run())
        assert "diagnosis" in result.get("sub_agent_outputs", {})
        assert "escalation" in result.get("sub_agent_outputs", {})
        tickets = db_session.query(Ticket).all()
        assert len(tickets) >= 1, "协作流程应自动创建工单"

    def test_simple_question_no_escalation(self, db_session: Session):
        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "general",
                "default": "你好！有什么可以帮你的？",
            }
        )
        graph = build_supervisor_graph(llm=mock, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "你好"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        assert "escalation" not in result.get("sub_agent_outputs", {})
        tickets = db_session.query(Ticket).all()
        assert len(tickets) == 0

    def test_diagnosis_no_match_no_escalation(self, db_session: Session):
        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "diagnosis",
                "default": "未匹配已知错误模式，建议检查日志。",
            }
        )
        graph = build_supervisor_graph(llm=mock, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "奇怪的错误"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "UNKNOWN_ERR",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        assert "escalation" not in result.get("sub_agent_outputs", {})
