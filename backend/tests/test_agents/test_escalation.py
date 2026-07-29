import asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from sqlalchemy.orm import Session
from app.agents.supervisor import build_supervisor_graph, AgentState
from app.models.error_pattern import ErrorPattern
from app.models.ticket import Ticket
from tests.mock_providers import MockLLMProvider


class TestEscalationAgent:
    def test_escalation_creates_ticket(self, db_session: Session):
        ep = ErrorPattern(pattern="CRIT_ERR", severity="critical", solution="立即修复")
        db_session.add(ep)
        db_session.commit()

        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "diagnosis",
                "default": "系统出现严重错误，需要升级处理。",
            }
        )
        checkpointer = MemorySaver()
        graph = build_supervisor_graph(
            llm=mock, session=db_session, checkpointer=checkpointer
        )
        state: AgentState = {
            "messages": [{"role": "user", "content": "出现 CRIT_ERR 错误"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "CRIT_ERR",
            "citations": [],
        }

        async def run():
            await graph.ainvoke(state, config={"configurable": {"thread_id": "esc-1"}})
            result = await graph.ainvoke(
                Command(resume={"approved": True}),
                config={"configurable": {"thread_id": "esc-1"}},
            )
            return result

        result = asyncio.run(run())
        assert "diagnosis" in result.get("sub_agent_outputs", {})

        tickets = db_session.query(Ticket).all()
        assert len(tickets) >= 1, "应自动创建工单"

    def test_low_severity_no_escalation(self, db_session: Session):
        ep = ErrorPattern(pattern="WARN_001", severity="low", solution="重启服务")
        db_session.add(ep)
        db_session.commit()

        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "diagnosis",
                "default": "这是一个低严重度警告，请重启服务。",
            }
        )
        graph = build_supervisor_graph(llm=mock, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "看到 WARN_001 警告"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "WARN_001",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        asyncio.run(run())
        tickets = db_session.query(Ticket).all()
        assert len(tickets) == 0, "低严重度不应创建工单"
