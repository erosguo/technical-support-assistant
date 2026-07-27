import asyncio
import math
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.chunking import chunk_text
from app.services.llm import LLMRouter


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vector dimension mismatch")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def index_document(
    session: Session,
    llm: LLMRouter,
    doc: KnowledgeDocument,
) -> dict:
    chunks = chunk_text(doc.content)
    texts = [c["content"] for c in chunks]
    embeddings = asyncio.run(llm.embed_batch(texts)) if texts else []

    for chunk_data, embedding in zip(chunks, embeddings):
        chunk = DocumentChunk(
            document_id=doc.id,
            content=chunk_data["content"],
            chunk_index=chunk_data["chunk_index"],
            embedding=embedding,
        )
        session.add(chunk)
        session.flush()

    session.commit()
    return {"chunks_created": len(chunks)}


def search_chunks(
    session: Session,
    llm: LLMRouter,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    query_embedding = asyncio.run(llm.embed(query))
    chunks = session.query(DocumentChunk).all()

    scored = []
    for chunk in chunks:
        if chunk.embedding is None:
            continue
        doc = (
            session.query(KnowledgeDocument)
            .filter(KnowledgeDocument.id == chunk.document_id)
            .first()
        )
        score = cosine_similarity(query_embedding, chunk.embedding)
        scored.append(
            {
                "content": chunk.content,
                "document_id": str(chunk.document_id),
                "document_title": doc.title if doc else "Unknown",
                "chunk_index": chunk.chunk_index,
                "score": score,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
