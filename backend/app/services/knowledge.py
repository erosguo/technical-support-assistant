from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument


def create_document(
    session: Session,
    title: str,
    content: str,
    doc_type: str = "markdown",
) -> KnowledgeDocument:
    doc = KnowledgeDocument(
        title=title,
        content=content,
        doc_type=doc_type,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def search_knowledge(
    session: Session,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    result = session.execute(select(KnowledgeDocument).limit(top_k))
    return [
        {"id": str(doc.id), "title": doc.title, "content": doc.content[:200]}
        for doc in result.scalars().all()
    ]
