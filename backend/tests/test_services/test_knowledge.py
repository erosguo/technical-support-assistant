from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument
from app.services.knowledge import create_document


class TestKnowledgeService:
    def test_create_document_returns_doc(self, db_session: Session):
        doc = create_document(
            session=db_session,
            title="测试文档",
            content="# Hello",
            doc_type="markdown",
        )
        assert doc.id is not None
        assert doc.title == "测试文档"
        assert doc.content == "# Hello"

    def test_create_document_persists_to_db(self, db_session: Session):
        create_document(session=db_session, title="持久化测试", content="data")
        from sqlalchemy import select

        result = db_session.execute(select(KnowledgeDocument))
        docs = result.scalars().all()
        assert len(docs) == 1
        assert docs[0].title == "持久化测试"

    def test_create_document_default_doc_type(self, db_session: Session):
        doc = create_document(session=db_session, title="默认类型", content="data")
        assert doc.doc_type == "markdown"
