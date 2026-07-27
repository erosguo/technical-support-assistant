import uuid
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.models.conversation import Conversation, Message


class TestKnowledgeDocument:
    def test_create_document(self, db_session: Session):
        doc = KnowledgeDocument(
            title="测试文档", content="# Test Content", doc_type="markdown"
        )
        db_session.add(doc)
        db_session.commit()
        assert doc.id is not None
        if isinstance(doc.id, uuid.UUID):
            pass
        else:
            uuid.UUID(str(doc.id))  # validates it's a valid UUID string

    def test_document_chunk_relation(self, db_session: Session):
        doc = KnowledgeDocument(title="Doc with chunks", content="Chunked content")
        db_session.add(doc)
        db_session.flush()

        chunk = DocumentChunk(document_id=doc.id, content="chunk 1", chunk_index=0)
        db_session.add(chunk)
        db_session.commit()

        assert chunk.id is not None
        assert chunk.document_id == doc.id

    def test_timestamps_auto_set(self, db_session: Session):
        doc = KnowledgeDocument(title="Timestamps", content="test")
        db_session.add(doc)
        db_session.commit()
        assert doc.created_at is not None
        assert doc.updated_at is not None


class TestConversation:
    def test_create_conversation(self, db_session: Session):
        conv = Conversation(title="测试会话")
        db_session.add(conv)
        db_session.commit()
        assert conv.id is not None
        assert conv.status == "active"

    def test_add_message(self, db_session: Session):
        conv = Conversation(title="会话消息测试")
        db_session.add(conv)
        db_session.flush()

        msg = Message(conversation_id=conv.id, role="user", content="你好")
        db_session.add(msg)
        db_session.commit()

        assert msg.id is not None
        assert msg.role == "user"
        assert msg.content == "你好"

    def test_message_default_sources(self, db_session: Session):
        conv = Conversation(title="默认值测试")
        db_session.add(conv)
        db_session.flush()

        msg = Message(conversation_id=conv.id, role="assistant", content="回复")
        db_session.add(msg)
        db_session.commit()

        assert msg.sources == []
        assert msg.tokens_used == 0
