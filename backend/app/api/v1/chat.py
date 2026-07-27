import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.models.conversation import Conversation, Message
from app.agents.supervisor import build_supervisor_graph
from app.services.knowledge import search_knowledge

router = APIRouter()


def _conv_to_dict(conv: Conversation) -> dict:
    return {
        "id": str(conv.id),
        "title": conv.title,
        "status": conv.status,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
    }


@router.get("/conversations")
def list_conversations(session: Session = Depends(get_session)):
    result = session.execute(
        select(Conversation).order_by(desc(Conversation.updated_at))
    )
    return [_conv_to_dict(c) for c in result.scalars().all()]


@router.post("/conversations")
def create_conversation(data: dict, session: Session = Depends(get_session)):
    conv = Conversation(title=data.get("title", "新对话"))
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return _conv_to_dict(conv)


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: str, session: Session = Depends(get_session)):
    conv = session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "会话不存在")
    return _conv_to_dict(conv)


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str, session: Session = Depends(get_session)):
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
def list_messages(conv_id: str, session: Session = Depends(get_session)):
    result = session.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    return [_msg_to_dict(m) for m in result.scalars().all()]


@router.post("/completions")
def chat_completion(req: dict, session: Session = Depends(get_session)):
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

    ctx = search_knowledge(session, content)
    graph = build_supervisor_graph()
    state = {
        "messages": [{"role": "user", "content": content}],
        "user_intent": "",
        "sub_agent_outputs": {},
        "knowledge_context": [c["content"] for c in ctx],
        "error_info": "",
    }

    async def run_agent():
        full_content = ""
        async for chunk in graph.astream(state):
            for node_output in chunk.values():
                msgs = node_output.get("messages", [])
                for msg in msgs:
                    if msg["role"] == "assistant":
                        full_content = msg["content"]
        return full_content

    full_content = asyncio.run(run_agent())

    def event_stream():
        yield f"data: {json.dumps({'content': full_content, 'conversation_id': str(conv_id), 'sources': ctx})}\n\n"
        yield "data: [DONE]\n\n"

    msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=full_content,
        agent_name=state.get("user_intent", "general"),
        sources=ctx,
    )
    session.add(msg)
    session.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
