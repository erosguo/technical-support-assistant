import uuid
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), default="新对话")
    status = Column(String(50), default="active")
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True, index=True)
    metadata_ = Column("metadata", JSON, default=dict)


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        GUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    agent_name = Column(String(100), nullable=True)
    sources = Column(JSON, default=list)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)
