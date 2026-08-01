import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.agents.supervisor import build_supervisor_graph
from app.core.config import settings
from app.services.auth import get_current_user
from app.services.knowledge import search_knowledge
from app.services.llm import LLMRouter

router = APIRouter()

checkpointer = MemorySaver()


def _conv_to_dict(conv: Conversation) -> dict:
    return {
        "id": str(conv.id),
        "title": conv.title,
        "status": conv.status,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
    }


@router.get("/conversations")
def list_conversations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = session.execute(
        select(Conversation).order_by(desc(Conversation.updated_at))
    )
    return [_conv_to_dict(c) for c in result.scalars().all()]


@router.post("/conversations")
def create_conversation(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    conv = Conversation(title=data.get("title", "新对话"))
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return _conv_to_dict(conv)


@router.get("/conversations/{conv_id}")
def get_conversation(
    conv_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    conv = session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "会话不存在")
    return _conv_to_dict(conv)


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    conv = session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "会话不存在")
    session.delete(conv)
    session.commit()
    return {"ok": True}


def _msg_to_dict(msg: Message) -> dict:
    return {
        "id": str(msg.id),
        "role": msg.role,
        "content": msg.content,
        "agent_name": msg.agent_name,
        "sources": msg.sources or [],
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


@router.get("/conversations/{conv_id}/messages")
def list_messages(
    conv_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = session.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    return [_msg_to_dict(m) for m in result.scalars().all()]


@router.post("/completions")
def chat_completion(
    req: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    content = req["content"]
    conv_id = req.get("conversation_id")

    if not conv_id:
        conv = Conversation(title=content[:50])
        session.add(conv)
        session.commit()
        conv_id = str(conv.id)
    else:
        conv = session.get(Conversation, conv_id)
        if not conv:
            raise HTTPException(404, "会话不存在")

    user_msg = Message(conversation_id=conv_id, role="user", content=content)
    session.add(user_msg)
    session.commit()

    ctx = (
        search_knowledge(session=session, llm=LLMRouter(), query=content)
        if settings.llm_api_key
        else []
    )
    graph = build_supervisor_graph(session=session, checkpointer=checkpointer)
    state = {
        "messages": [{"role": "user", "content": content}],
        "user_intent": "",
        "sub_agent_outputs": {},
        "knowledge_context": ctx,
        "error_info": content,
    }

    async def run_agent():
        return await graph.ainvoke(
            state, config={"configurable": {"thread_id": str(conv_id)}}
        )

    result = asyncio.run(run_agent())
    interrupts = result.get("__interrupt__", [])

    if interrupts:
        payload = getattr(interrupts[0], "value", interrupts[0])

        def interrupt_stream():
            yield f"data: {json.dumps({'interrupt': payload, 'conversation_id': str(conv_id)})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(interrupt_stream(), media_type="text/event-stream")

    full_content = ""
    for msg in result.get("messages", []):
        if msg["role"] == "assistant":
            full_content = msg["content"]
    citations = result.get("citations", [])
    sources = citations or ctx

    def event_stream():
        yield f"data: {json.dumps({'content': full_content, 'conversation_id': str(conv_id)})}\n\n"
        if sources:
            yield f"data: {json.dumps({'citations': sources})}\n\n"
        yield "data: [DONE]\n\n"

    msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=full_content,
        agent_name=result.get("user_intent", "general"),
        sources=sources,
    )
    session.add(msg)
    session.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/completions/resume")
def chat_resume(
    req: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    conv_id = req.get("conversation_id")
    approved = bool(req.get("approved", False))
    if not conv_id:
        raise HTTPException(400, "缺少 conversation_id")

    graph = build_supervisor_graph(session=session, checkpointer=checkpointer)

    async def run_resume():
        return await graph.ainvoke(
            Command(resume={"approved": approved}),
            config={"configurable": {"thread_id": str(conv_id)}},
        )

    result = asyncio.run(run_resume())

    full_content = ""
    for msg in result.get("messages", []):
        if msg["role"] == "assistant":
            full_content = msg["content"]
    citations = result.get("citations", [])
    sources = citations or []
    decision = result.get("sub_agent_outputs", {}).get("human_decision", "rejected")

    def event_stream():
        yield f"data: {json.dumps({'content': full_content, 'conversation_id': str(conv_id)})}\n\n"
        if sources:
            yield f"data: {json.dumps({'citations': sources})}\n\n"
        yield f"data: {json.dumps({'decision': decision})}\n\n"
        yield "data: [DONE]\n\n"

    msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=full_content,
        agent_name="escalation",
        sources=sources,
    )
    session.add(msg)
    session.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
