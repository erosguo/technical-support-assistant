"""AuditLog model — records all significant user operations.

PRD 6.3 Security: full operation logging, retained for 180 days.
"""

import uuid
from sqlalchemy import Column, String, Text, JSON
from app.db.base import Base, TimestampMixin
from app.db.guid import GUID


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)  # create/update/delete/login/etc.
    resource_type = Column(String(50), nullable=True)  # ticket/knowledge/user/etc.
    resource_id = Column(String(36), nullable=True)
    method = Column(String(10), nullable=True)  # GET/POST/PATCH/DELETE
    path = Column(String(500), nullable=True)
    status_code = Column(String(10), nullable=True)  # "200", "404", etc.
    detail = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
