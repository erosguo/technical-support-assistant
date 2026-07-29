from typing import Literal, TypedDict
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from app.services.llm import LLMRouter
from app.agents.diagnosis import diagnosis_node


class AgentState(TypedDict):
    messages: list[dict]
    user_intent: str
    sub_agent_outputs: dict
    knowledge_context: list
    error_info: str
    citations: list[dict]


INTENT_PROMPT = """分析用户问题的意图，只返回一个词：
- knowledge: 知识问答、产品使用问题
- diagnosis: 故障排查、报错分析
- general: 一般性对话
问题：{query}"""


CITATION_PROMPT = """基于以下知识回答问题。请在你的回答末尾标注引用来源，格式为【来源: 文档名称】。
如果知识不足以回答，请如实说明。

知识：
{context}

问题：{query}"""


def _format_chunks(knowledge_context: list) -> str:
    parts = []
    for item in knowledge_context:
        if isinstance(item, dict):
            title = item.get("document_title", "未知文档")
            content = item.get("content", str(item))
            parts.append(f"[{title}] {content}")
        else:
            parts.append(str(item))
    return "\n\n".join(parts) if parts else "未找到相关知识。"


def _extract_citations(knowledge_context: list) -> list[dict]:
    citations = []
    for item in knowledge_context:
        if isinstance(item, dict) and "document_title" in item:
            citations.append(
                {
                    "document_id": item.get("document_id", ""),
                    "document_title": item["document_title"],
                    "chunk_index": item.get("chunk_index", 0),
                    "score": item.get("score", 0.0),
                    "excerpt": item.get("content", "")[:200],
                }
            )
    return citations


def build_supervisor_graph(llm: LLMRouter = None, session: Session = None):
    llm = llm or LLMRouter()

    async def detect_intent(state: AgentState) -> AgentState:
        query = state["messages"][-1]["content"]
        intent = await llm.chat(
            messages=[{"role": "user", "content": INTENT_PROMPT.format(query=query)}],
            temperature=0,
            max_tokens=20,
        )
        state["user_intent"] = intent.strip().lower()
        if state["user_intent"] not in ("knowledge", "diagnosis"):
            state["user_intent"] = "general"
        return state

    async def knowledge_node(state: AgentState) -> AgentState:
        query = state["messages"][-1]["content"]
        ctx = state.get("knowledge_context", [])
        context = _format_chunks(ctx)
        prompt = CITATION_PROMPT.format(context=context, query=query)
        reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
        state["messages"].append({"role": "assistant", "content": reply})
        state["citations"] = _extract_citations(ctx)
        return state

    async def general_node(state: AgentState) -> AgentState:
        reply = await llm.chat(messages=state["messages"])
        state["messages"].append({"role": "assistant", "content": reply})
        return state

    async def diagnosis_wrapper(state: AgentState) -> AgentState:
        return await diagnosis_node(state, llm, session)

    def router_condition(
        state: AgentState,
    ) -> Literal["knowledge", "diagnosis", "general"]:
        intent = state.get("user_intent", "general")
        return intent

    graph = StateGraph(AgentState)
    graph.add_node("detect_intent", detect_intent)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("diagnosis", diagnosis_wrapper)
    graph.add_node("general", general_node)
    graph.set_entry_point("detect_intent")
    graph.add_conditional_edges("detect_intent", router_condition)
    graph.add_edge("knowledge", END)
    graph.add_edge("diagnosis", END)
    graph.add_edge("general", END)
    return graph.compile()
