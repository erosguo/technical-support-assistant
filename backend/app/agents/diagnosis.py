from sqlalchemy.orm import Session
from app.services.diagnosis import match_errors

DIAGNOSIS_PROMPT = """你是故障诊断专家。根据以下错误信息和已知模式给出诊断建议。
如果已知解决方案为空，给出通用排查步骤。

错误信息：{error_text}

已知匹配模式：
{matches}

请给出诊断结果和修复建议。"""

NO_MATCH_PROMPT = """你是故障诊断专家。以下错误信息没有匹配已知模式。
请给出通用排查步骤和建议。

错误信息：{error_text}

请给出诊断结果和修复建议。"""


def format_matches(matches: list[dict]) -> str:
    if not matches:
        return "无匹配模式"
    lines = []
    for m in matches:
        sev = m.get("severity", "unknown")
        sol = m.get("solution") or "无预设解决方案"
        lines.append(f"- [严重度: {sev}] 模式「{m['pattern']}」→ {sol}")
    return "\n".join(lines)


async def diagnosis_node(state: dict, llm, session: Session = None) -> dict:
    error_text = state.get("error_info", state["messages"][-1]["content"])

    if session is not None:
        matches = match_errors(session, error_text)
    else:
        matches = []

    if matches:
        prompt = DIAGNOSIS_PROMPT.format(
            error_text=error_text, matches=format_matches(matches)
        )
    else:
        prompt = NO_MATCH_PROMPT.format(error_text=error_text)

    reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
    state["messages"].append({"role": "assistant", "content": reply})
    state["sub_agent_outputs"]["diagnosis"] = {
        "matches": matches,
        "reply": reply,
        "needs_escalation": any(
            m.get("severity") in ("critical", "high") for m in matches
        ),
    }
    return state
