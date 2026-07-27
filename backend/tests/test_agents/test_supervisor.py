import asyncio
import pytest
from app.agents.supervisor import build_supervisor_graph, AgentState
from tests.mock_providers import MockLLMProvider


@pytest.fixture
def mock_provider():
    return MockLLMProvider(
        responses={
            "configure_ssl": "knowledge",
            "error_12345": "diagnosis",
            "hello_hi": "general",
        }
    )


class TestSupervisorAgent:
    def test_detect_knowledge_intent(self, mock_provider):
        graph = build_supervisor_graph(llm=mock_provider)
        state: AgentState = {
            "messages": [
                {"role": "user", "content": "how to configure_ssl certificate?"}
            ],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        assert result["user_intent"] == "knowledge"

    def test_detect_general_intent(self, mock_provider):
        graph = build_supervisor_graph(llm=mock_provider)
        state: AgentState = {
            "messages": [{"role": "user", "content": "hello_hi"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        assert result["user_intent"] == "general"

    def test_knowledge_node_returns_reply(self, mock_provider):
        mock_provider.responses["default"] = "根据知识库，配置SSL的步骤是..."
        graph = build_supervisor_graph(llm=mock_provider)
        state: AgentState = {
            "messages": [{"role": "user", "content": "how to configure_ssl?"}],
            "user_intent": "knowledge",
            "sub_agent_outputs": {},
            "knowledge_context": [
                "SSL证书配置步骤：1. 生成CSR 2. 提交验证 3. 部署证书"
            ],
            "error_info": "",
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert len(last_msg["content"]) > 0

    def test_knowledge_node_receives_structured_chunks(self, mock_provider):
        mock_provider.responses["default"] = "根据文档'SSL指南'中的内容..."
        graph = build_supervisor_graph(llm=mock_provider)
        state: AgentState = {
            "messages": [{"role": "user", "content": "how to configure_ssl?"}],
            "user_intent": "knowledge",
            "sub_agent_outputs": {},
            "knowledge_context": [
                {
                    "content": "生成CSR是第一步",
                    "document_title": "SSL指南",
                    "chunk_index": 0,
                    "score": 0.95,
                }
            ],
            "error_info": "",
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert len(last_msg["content"]) > 0

    def test_knowledge_node_populates_citations(self, mock_provider):
        mock_provider.responses["default"] = "根据文档'SSL指南'中的内容..."
        graph = build_supervisor_graph(llm=mock_provider)
        chunks = [
            {
                "content": "生成CSR是第一步",
                "document_title": "SSL指南",
                "chunk_index": 0,
                "score": 0.95,
                "document_id": "doc-1",
            }
        ]
        state: AgentState = {
            "messages": [{"role": "user", "content": "how to configure_ssl?"}],
            "user_intent": "knowledge",
            "sub_agent_outputs": {},
            "knowledge_context": chunks,
            "error_info": "",
        }

        async def run():
            return await graph.ainvoke(state)

        result = asyncio.run(run())
        assert "citations" in result
        assert len(result["citations"]) >= 1
        assert result["citations"][0]["document_title"] == "SSL指南"

    def test_graph_compiles_without_error(self):
        graph = build_supervisor_graph()
        assert graph is not None
