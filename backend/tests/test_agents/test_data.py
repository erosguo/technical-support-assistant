import asyncio
from sqlalchemy.orm import Session
from app.agents.supervisor import build_supervisor_graph, AgentState
from app.models.conversation import Conversation
from tests.mock_providers import MockLLMProvider


class TestDataAgent:
    def test_data_agent_returns_statistics(self, db_session: Session):
        conv = Conversation(title="测试对话")
        db_session.add(conv)
        db_session.commit()

        mock_provider = MockLLMProvider(
            responses={
                "分析用户问题的意图": "data",
                "default": "当前系统共有 1 个对话。",
            }
        )
        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "有多少对话？"}],
            "user_intent": "data",
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
        assert "data" in result.get("sub_agent_outputs", {})

    def test_data_agent_knowledge_stats(self, db_session: Session):
        from app.models.knowledge import KnowledgeDocument

        db_session.add(KnowledgeDocument(title="doc1", content="c1"))
        db_session.commit()

        mock_provider = MockLLMProvider(
            responses={
                "分析用户问题的意图": "data",
                "default": "知识库有 1 个文档。",
            }
        )
        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "知识库有多少文档？"}],
            "user_intent": "data",
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

    def test_data_agent_unknown_query(self, db_session: Session):
        mock_provider = MockLLMProvider(
            responses={
                "分析用户问题的意图": "data",
                "default": "抱歉，我能查询对话统计、消息统计和知识库统计，请具体描述您的问题。",
            }
        )
        graph = build_supervisor_graph(llm=mock_provider, session=db_session)
        state: AgentState = {
            "messages": [{"role": "user", "content": "今天天气怎么样？"}],
            "user_intent": "data",
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
