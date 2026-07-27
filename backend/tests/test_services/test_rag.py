import pytest
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.rag import index_document, search_chunks, cosine_similarity
from tests.mock_providers import MockLLMProvider


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_mismatched_length_raises(self):
        with pytest.raises(ValueError):
            cosine_similarity([1.0], [1.0, 2.0])


class TestIndexDocument:
    def test_index_document_creates_chunks(self, db_session: Session):
        llm = MockLLMProvider()
        doc = KnowledgeDocument(title="Test", content="hello world foo bar baz qux")
        db_session.add(doc)
        db_session.commit()

        result = index_document(session=db_session, llm=llm, doc=doc)
        assert result["chunks_created"] >= 1

    def test_chunks_have_embeddings(self, db_session: Session):
        llm = MockLLMProvider()
        doc = KnowledgeDocument(title="Embed test", content="some content to embed")
        db_session.add(doc)
        db_session.commit()

        index_document(session=db_session, llm=llm, doc=doc)
        chunks = (
            db_session.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc.id)
            .all()
        )
        for chunk in chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 3  # matches MockLLMProvider dimension


class TestSearchChunks:
    def test_search_returns_top_k(self, db_session: Session):
        llm = MockLLMProvider()
        doc = KnowledgeDocument(title="Searchable", content="content for searching")
        db_session.add(doc)
        db_session.commit()
        index_document(session=db_session, llm=llm, doc=doc)

        results = search_chunks(session=db_session, llm=llm, query="test", top_k=2)
        assert len(results) <= 2
        assert len(results) > 0

    def test_search_result_has_citation_fields(self, db_session: Session):
        llm = MockLLMProvider()
        doc = KnowledgeDocument(title="Citation Test", content="citation content")
        db_session.add(doc)
        db_session.commit()
        index_document(session=db_session, llm=llm, doc=doc)

        results = search_chunks(session=db_session, llm=llm, query="test", top_k=1)
        assert len(results) == 1
        r = results[0]
        assert "content" in r
        assert "document_id" in r
        assert "document_title" in r
        assert "chunk_index" in r
        assert "score" in r

    def test_search_empty_db_returns_empty(self, db_session: Session):
        llm = MockLLMProvider()
        results = search_chunks(session=db_session, llm=llm, query="anything", top_k=5)
        assert results == []
