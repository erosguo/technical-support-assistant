import asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from sqlalchemy.orm import Session
from app.agents.supervisor import build_supervisor_graph, AgentState
from app.models.error_pattern import ErrorPattern
from app.models.ticket import Ticket
from tests.mock_providers import MockLLMProvider

THREAD_ID = "test-interrupt-1"


class TestHumanInTheLoop:
    def test_interrupt_at_escalation(self, db_session: Session):
        ep = ErrorPattern(pattern="CRIT_ERR", severity="critical", solution="紧急修复")
        db_session.add(ep)
        db_session.commit()

        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "diagnosis",
                "default": "严重错误，需要升级。",
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
            result = await graph.ainvoke(
                state,
                config={"configurable": {"thread_id": THREAD_ID}},
            )
            return result

        result = asyncio.run(run())
        tickets_before = db_session.query(Ticket).count()
        assert tickets_before == 0, "中断期间不应创建工单"
        assert result["messages"][-1]["role"] == "assistant"

    def test_approve_escalation_resumes(self, db_session: Session):
        ep = ErrorPattern(pattern="SEVERE", severity="high", solution="排查日志")
        db_session.add(ep)
        db_session.commit()

        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "diagnosis",
                "default": "高严重度错误，需要升级处理。",
            }
        )
        checkpointer = MemorySaver()
        graph = build_supervisor_graph(
            llm=mock, session=db_session, checkpointer=checkpointer
        )
        state: AgentState = {
            "messages": [{"role": "user", "content": "出现 SEVERE 错误"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "SEVERE",
            "citations": [],
        }

        async def run():
            await graph.ainvoke(
                state,
                config={"configurable": {"thread_id": THREAD_ID}},
            )
            await graph.ainvoke(
                Command(resume={"approved": True}),
                config={"configurable": {"thread_id": THREAD_ID}},
            )

        asyncio.run(run())
        tickets = db_session.query(Ticket).all()
        assert len(tickets) >= 1, "批准后应创建工单"

    def test_reject_escalation_stops(self, db_session: Session):
        ep = ErrorPattern(pattern="WARN", severity="medium", solution="检查配置")
        db_session.add(ep)
        db_session.commit()

        mock = MockLLMProvider(
            responses={
                "分析用户问题的意图": "diagnosis",
                "default": "中等严重度，建议升级。",
            }
        )
        checkpointer = MemorySaver()
        graph = build_supervisor_graph(
            llm=mock, session=db_session, checkpointer=checkpointer
        )
        state: AgentState = {
            "messages": [{"role": "user", "content": "出现 WARN 错误"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "WARN",
            "citations": [],
        }

        async def run():
            await graph.ainvoke(
                state,
                config={"configurable": {"thread_id": THREAD_ID}},
            )
            await graph.ainvoke(
                Command(resume={"approved": False}),
                config={"configurable": {"thread_id": THREAD_ID}},
            )

        asyncio.run(run())
        tickets = db_session.query(Ticket).all()
        assert len(tickets) == 0, "拒绝后不应创建工单"
