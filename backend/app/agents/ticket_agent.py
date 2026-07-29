from sqlalchemy.orm import Session
from app.services.ticket import list_tickets, create_ticket

TICKET_PROMPT = """你是工单管理助手。根据用户请求执行工单操作。

用户请求：{query}

可用操作：
1. create — 创建工单（需要标题、描述、优先级）
2. list — 查看工单
3. update — 更新工单状态

请生成回复。"""


def _extract_ticket_action(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["创建", "新建", "新增", "开一个"]):
        return "create"
    if any(w in q for w in ["查看", "显示", "列出", "所有工单", "列表"]):
        return "list"
    if any(w in q for w in ["更新", "修改", "状态"]):
        return "update"
    return "create"


async def ticket_node(state: dict, llm, session: Session = None) -> dict:
    escalation_ctx = state.get("sub_agent_outputs", {}).get("escalation", {})
    query = state["messages"][-1]["content"]

    output = {}

    if escalation_ctx.get("escalated") and session is not None:
        ticket = create_ticket(
            session=session,
            title=escalation_ctx.get("escalation_title", query[:50]),
            description=escalation_ctx.get("escalation_description", query),
            priority="high",
            source="escalation",
        )
        output["created_by_escalation"] = True
        output["ticket_id"] = str(ticket.id)
    else:
        action = _extract_ticket_action(query)
        if session is not None:
            if action == "list":
                tickets = list_tickets(session)
                output["tickets"] = [
                    {"id": str(t.id), "title": t.title, "status": t.status}
                    for t in tickets
                ]
            elif action == "update":
                tickets = list_tickets(session)
                output["tickets"] = [
                    {"id": str(t.id), "title": t.title, "status": t.status}
                    for t in tickets
                ]

    prompt = TICKET_PROMPT.format(query=query)
    reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
    state["messages"].append({"role": "assistant", "content": reply})
    state["sub_agent_outputs"]["ticket"] = output
    return state
