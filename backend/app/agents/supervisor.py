from typing import Literal, TypedDict
from langgraph.graph import StateGraph, END
from app.services.llm import LLMRouter


class AgentState(TypedDict):
    messages: list[dict]
    user_intent: str
    sub_agent_outputs: dict
    knowledge_context: list
    error_info: str


INTENT_PROMPT = """分析用户问题的意图，只返回一个词：
- knowledge: 知识问答、产品使用问题
- diagnosis: 故障排查、报错分析
- general: 一般性对话
问题：{query}"""


def build_supervisor_graph(llm: LLMRouter = None):
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
        context = "\n\n".join(ctx) if ctx else "未找到相关知识。"
        prompt = f"""基于以下知识回答问题。如果知识不足以回答，请如实说明。
知识：{context}
问题：{query}"""
        reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
        state["messages"].append({"role": "assistant", "content": reply})
        return state

    async def general_node(state: AgentState) -> AgentState:
        reply = await llm.chat(messages=state["messages"])
        state["messages"].append({"role": "assistant", "content": reply})
        return state

    def router_condition(state: AgentState) -> Literal["knowledge", "general"]:
        intent = state.get("user_intent", "general")
        if intent == "diagnosis":
            return "general"
        return intent

    graph = StateGraph(AgentState)
    graph.add_node("detect_intent", detect_intent)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("general", general_node)
    graph.set_entry_point("detect_intent")
    graph.add_conditional_edges("detect_intent", router_condition)
    graph.add_edge("knowledge", END)
    graph.add_edge("general", END)
    return graph.compile()
