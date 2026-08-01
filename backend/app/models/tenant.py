import uuid
from sqlalchemy import Column, String, Boolean, JSON
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)
