import uuid
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer, PickleType
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    doc_type = Column(String(50), default="markdown")
    metadata_ = Column("metadata", JSON, default=dict)


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    document_id = Column(
        GUID, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    embedding = Column(PickleType, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
