import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.services.llm import LLMRouter
from app.agents.diagnosis import diagnosis_node
from app.models.conversation import Conversation, Message

router = APIRouter()


class DiagnosisRequest(BaseModel):
    error_text: str
    conversation_id: str | None = None


@router.post("/diagnosis")
def diagnose(req: DiagnosisRequest, session: Session = Depends(get_session)):
    llm = LLMRouter()

    state = {
        "messages": [{"role": "user", "content": req.error_text}],
        "user_intent": "diagnosis",
        "sub_agent_outputs": {},
        "knowledge_context": [],
        "error_info": req.error_text,
        "citations": [],
    }

    async def run():
        return await diagnosis_node(state, llm, session)

    result = asyncio.run(run())
    diag = result.get("sub_agent_outputs", {}).get("diagnosis", {})
    reply = result["messages"][-1]["content"]

    if req.conversation_id:
        conv = session.get(Conversation, req.conversation_id)
        if conv:
            user_msg = Message(
                conversation_id=req.conversation_id,
                role="user",
                content=req.error_text,
                agent_name="diagnosis",
            )
            assistant_msg = Message(
                conversation_id=req.conversation_id,
                role="assistant",
                content=reply,
                agent_name="diagnosis",
                sources=diag.get("matches", []),
            )
            session.add_all([user_msg, assistant_msg])
            session.commit()

    return {
        "reply": reply,
        "matches": diag.get("matches", []),
        "needs_escalation": diag.get("needs_escalation", False),
        "conversation_id": req.conversation_id,
    }
