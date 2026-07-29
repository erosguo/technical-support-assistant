from sqlalchemy.orm import Session
from app.services.data_query import (
    count_conversations,
    count_messages,
    count_knowledge_documents,
    recent_conversations,
)
from app.models.conversation import Conversation, Message


class TestDataQuery:
    def test_count_conversations_empty(self, db_session: Session):
        assert count_conversations(db_session) == 0

    def test_count_conversations_with_data(self, db_session: Session):
        db_session.add(Conversation(title="c1"))
        db_session.flush()
        db_session.add(Conversation(title="c2"))
        db_session.commit()
        assert count_conversations(db_session) == 2

    def test_count_messages_empty(self, db_session: Session):
        assert count_messages(db_session) == 0

    def test_count_messages_with_data(self, db_session: Session):
        conv = Conversation(title="c")
        db_session.add(conv)
        db_session.commit()
        msg1 = Message(conversation_id=conv.id, role="user", content="hi")
        msg2 = Message(conversation_id=conv.id, role="assistant", content="hello")
        db_session.add(msg1)
        db_session.flush()
        db_session.add(msg2)
        db_session.commit()
        assert count_messages(db_session) == 2

    def test_recent_conversations(self, db_session: Session):
        db_session.add(Conversation(title="old"))
        db_session.flush()
        db_session.add(Conversation(title="recent"))
        db_session.commit()
        result = recent_conversations(db_session, days=7)
        assert len(result) >= 1

    def test_count_knowledge_documents(self, db_session: Session):
        from app.models.knowledge import KnowledgeDocument

        db_session.add(KnowledgeDocument(title="d1", content="c1"))
        db_session.flush()
        db_session.add(KnowledgeDocument(title="d2", content="c2"))
        db_session.commit()
        assert count_knowledge_documents(db_session) == 2
