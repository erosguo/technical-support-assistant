from sqlalchemy.orm import Session

ESCALATION_PROMPT = """你是升级处理助手。根据诊断结果判断是否需要升级。
如需升级，将自动创建工单并通知相关工程师。

诊断结果：{diagnosis_result}
需升级：{needs_escalation}

请给出升级处理说明。"""


async def escalation_node(state: dict, llm, session: Session = None) -> dict:
    query = state["messages"][-1]["content"]
    diag = state.get("sub_agent_outputs", {}).get("diagnosis", {})
    matches = diag.get("matches", [])
    needs_escalation = diag.get("needs_escalation", False)

    output = {"escalated": False, "notified": False}

    if needs_escalation:
        title = f"[升级] {query[:50]}"
        desc_lines = []
        for m in matches:
            desc_lines.append(
                f"- [{m.get('severity', '')}] {m.get('pattern', '')}: {m.get('solution', '')}"
            )
        output["escalated"] = True
        output["escalation_title"] = title
        output["escalation_description"] = "\n".join(desc_lines) or query
        output["notified"] = True

    prompt = ESCALATION_PROMPT.format(
        diagnosis_result=str(matches),
        needs_escalation=str(needs_escalation),
    )
    reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
    state["messages"].append({"role": "assistant", "content": reply})
    state["sub_agent_outputs"]["escalation"] = output
    return state
