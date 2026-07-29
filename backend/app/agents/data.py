from sqlalchemy.orm import Session
from app.services.data_query import (
    count_conversations,
    count_messages,
    recent_conversations,
    knowledge_stats,
)

DATA_PROMPT = """你是数据分析助手。根据用户问题查询系统数据，用自然语言回复。
可用数据源：对话统计、消息统计、知识库统计。

用户问题：{query}

数据结果：
{data_result}"""


async def data_node(state: dict, llm, session: Session = None) -> dict:
    query = state["messages"][-1]["content"]
    output = {}

    if session is not None:
        q = query.lower()
        data_lines = []
        if any(w in q for w in ["对话", "会话"]):
            conv_count = count_conversations(session)
            data_lines.append(f"对话总数：{conv_count}")
            if any(w in q for w in ["最近", "近", "天"]):
                recent = recent_conversations(session, days=7)
                data_lines.append(f"最近7天对话数：{len(recent)}")
        if any(w in q for w in ["消息"]):
            msg_count = count_messages(session)
            data_lines.append(f"消息总数：{msg_count}")
        if any(w in q for w in ["知识库", "文档", "知识"]):
            stats = knowledge_stats(session)
            data_lines.append(
                f"文档数：{stats['documents']}，分块数：{stats['chunks']}"
            )
        if not data_lines:
            data_lines.append(
                "可查询的数据维度：对话数、消息数、知识库文档数。请具体描述您的问题。"
            )
        output["data"] = data_lines
        data_result = "\n".join(data_lines)
    else:
        data_result = "无数据访问权限"

    prompt = DATA_PROMPT.format(query=query, data_result=data_result)
    reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
    state["messages"].append({"role": "assistant", "content": reply})
    state["sub_agent_outputs"]["data"] = output
    return state
