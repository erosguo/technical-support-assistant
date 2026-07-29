import uuid
from sqlalchemy import Column, String, Text, ForeignKey
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="open")
    priority = Column(String(20), default="medium")
    assigned_to = Column(String(100), nullable=True)
    source = Column(String(50), default="chat")
    conversation_id = Column(
        GUID, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
