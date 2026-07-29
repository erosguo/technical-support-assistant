import uuid
from sqlalchemy import Column, String, Text, JSON
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class ErrorPattern(Base, TimestampMixin):
    __tablename__ = "error_patterns"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    pattern = Column(String(500), nullable=False)
    solution = Column(Text, nullable=True)
    severity = Column(String(20), default="medium")
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
