from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeDocument, DocumentChunk


def count_conversations(session: Session) -> int:
    return session.execute(select(func.count(Conversation.id))).scalar() or 0


def count_messages(session: Session) -> int:
    return session.execute(select(func.count(Message.id))).scalar() or 0


def count_knowledge_documents(session: Session) -> int:
    return session.execute(select(func.count(KnowledgeDocument.id))).scalar() or 0


def recent_conversations(session: Session, days: int = 7) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(Conversation)
        .where(Conversation.created_at >= cutoff)
        .order_by(desc(Conversation.created_at))
    )
    result = session.execute(stmt)
    convs = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "status": c.status,
            "created_at": str(c.created_at),
        }
        for c in convs
    ]


def knowledge_stats(session: Session) -> dict:
    doc_count = count_knowledge_documents(session)
    chunk_count = session.execute(select(func.count(DocumentChunk.id))).scalar() or 0
    return {"documents": doc_count, "chunks": chunk_count}
