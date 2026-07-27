from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument
from app.services.rag import index_document, search_chunks
from app.services.llm import LLMRouter


def create_document(
    session: Session,
    title: str,
    content: str,
    doc_type: str = "markdown",
    llm: LLMRouter = None,
) -> KnowledgeDocument:
    doc = KnowledgeDocument(
        title=title,
        content=content,
        doc_type=doc_type,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    if llm is not None:
        index_document(session=session, llm=llm, doc=doc)

    return doc


def search_knowledge(
    session: Session,
    llm: LLMRouter,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    return search_chunks(session=session, llm=llm, query=query, top_k=top_k)
