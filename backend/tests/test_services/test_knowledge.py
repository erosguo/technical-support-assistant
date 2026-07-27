from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.knowledge import create_document, search_knowledge
from tests.mock_providers import MockLLMProvider


class TestCreateDocument:
    def test_creates_doc(self, db_session: Session):
        doc = create_document(
            session=db_session,
            title="测试文档",
            content="# Hello",
            doc_type="markdown",
        )
        assert doc.id is not None
        assert doc.title == "测试文档"
        assert doc.content == "# Hello"

    def test_persists_to_db(self, db_session: Session):
        create_document(session=db_session, title="持久化测试", content="data")
        from sqlalchemy import select

        result = db_session.execute(select(KnowledgeDocument))
        docs = result.scalars().all()
        assert len(docs) == 1
        assert docs[0].title == "持久化测试"

    def test_default_doc_type(self, db_session: Session):
        doc = create_document(session=db_session, title="默认类型", content="data")
        assert doc.doc_type == "markdown"


class TestIngestionPipeline:
    def test_create_with_llm_generates_chunks(self, db_session: Session):
        llm = MockLLMProvider()
        doc = create_document(
            session=db_session,
            title="Pipeline",
            content="word " * 200,
            llm=llm,
        )
        chunks = (
            db_session.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc.id)
            .all()
        )
        assert len(chunks) >= 1

    def test_chunks_have_embeddings(self, db_session: Session):
        llm = MockLLMProvider()
        doc = create_document(
            session=db_session,
            title="EmbedCheck",
            content="check embedding pipeline",
            llm=llm,
        )
        chunks = (
            db_session.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc.id)
            .all()
        )
        for c in chunks:
            assert c.embedding is not None
            assert len(c.embedding) == 3

    def test_delete_document_cascades_to_chunks(self, db_session: Session):
        llm = MockLLMProvider()
        doc = create_document(
            session=db_session,
            title="Cascade",
            content="word " * 200,
            llm=llm,
        )
        doc_id = doc.id
        db_session.delete(doc)
        db_session.commit()
        remaining = (
            db_session.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc_id)
            .count()
        )
        assert remaining == 0


class TestSearchKnowledge:
    def test_search_returns_citations(self, db_session: Session):
        llm = MockLLMProvider()
        create_document(
            session=db_session,
            title="Searchable",
            content="searchable content",
            llm=llm,
        )
        results = search_knowledge(session=db_session, llm=llm, query="search")
        assert len(results) > 0
        r = results[0]
        assert "content" in r
        assert "document_title" in r
        assert "score" in r
        assert "chunk_index" in r

    def test_search_empty_db(self, db_session: Session):
        llm = MockLLMProvider()
        results = search_knowledge(session=db_session, llm=llm, query="anything")
        assert results == []

    def test_search_respects_top_k(self, db_session: Session):
        llm = MockLLMProvider()
        for i in range(3):
            create_document(
                session=db_session,
                title=f"Doc{i}",
                content="word " * 100,
                llm=llm,
            )
        results = search_knowledge(session=db_session, llm=llm, query="test", top_k=2)
        assert len(results) <= 2
