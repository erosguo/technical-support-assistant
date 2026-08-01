import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, ForeignKey
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class DiagnosisFlow(Base, TimestampMixin):
    __tablename__ = "diagnosis_flows"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(
        JSON, nullable=False
    )  # [{id, title, description, conditions, next_step}]
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)
