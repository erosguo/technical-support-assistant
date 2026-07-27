from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.models.knowledge import KnowledgeDocument
from app.services.knowledge import create_document, search_knowledge

router = APIRouter()


@router.post("/documents")
def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    content = file.file.read().decode("utf-8")
    doc = create_document(session=session, title=title, content=content)
    return {"id": str(doc.id), "title": doc.title}


@router.get("/documents")
def list_documents(session: Session = Depends(get_session)):
    result = session.execute(
        select(KnowledgeDocument).order_by(desc(KnowledgeDocument.updated_at))
    )
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "doc_type": d.doc_type,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in result.scalars().all()
    ]


@router.get("/documents/{doc_id}")
def get_document(doc_id: str, session: Session = Depends(get_session)):
    doc = session.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return {
        "id": str(doc.id),
        "title": doc.title,
        "content": doc.content,
        "doc_type": doc.doc_type,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, session: Session = Depends(get_session)):
    doc = session.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    session.delete(doc)
    session.commit()
    return {"ok": True}


@router.post("/search")
def search_endpoint(
    query: str, top_k: int = 5, session: Session = Depends(get_session)
):
    results = search_knowledge(session, query, top_k=top_k)
    return {"results": results}
