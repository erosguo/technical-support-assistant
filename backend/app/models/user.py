import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        String(50), default="l1_engineer"
    )  # admin/manager/l2_engineer/l1_engineer
    is_active = Column(Boolean, default=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)
