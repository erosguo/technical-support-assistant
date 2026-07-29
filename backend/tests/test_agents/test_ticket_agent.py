import asyncio
from sqlalchemy.orm import Session
from app.agents.supervisor import build_supervisor_graph, AgentState
from tests.mock_providers import MockLLMProvider


class TestTicketAgent:
    def test_ticket_node_create(self, db_session: Session):
        mock_provider = MockLLMProvider(
            responses={
                "分析用户问题的意图": "ticket",
                "default": "已创建工单，标题：服务器宕机，优先级：critical",
            }
        )
        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "创建工单，服务器宕机，紧急"}],
            "user_intent": "ticket",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert "ticket" in result.get("sub_agent_outputs", {})

    def test_ticket_node_list(self, db_session: Session):
        mock_provider = MockLLMProvider(
            responses={
                "分析用户问题的意图": "ticket",
                "default": "当前有 0 个工单",
            }
        )
        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "查看所有工单"}],
            "user_intent": "ticket",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert "ticket" in result.get("sub_agent_outputs", {})

    def test_ticket_node_update(self, db_session: Session):
        from app.services.ticket import create_ticket

        ticket = create_ticket(
            session=db_session,
            title="测试工单",
            description="需要处理",
            priority="medium",
        )
        mock_provider = MockLLMProvider(
            responses={
                "分析用户问题的意图": "ticket",
                "default": f"已更新工单 {ticket.id} 状态为 in_progress",
            }
        )
        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [
                {"role": "user", "content": f"更新工单 {ticket.id} 状态为处理中"}
            ],
            "user_intent": "ticket",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
            "citations": [],
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
