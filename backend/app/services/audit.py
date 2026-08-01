"""Audit logging service — PRD 6.3 Security.

Records significant operations to the audit_logs table.
Designed to be called from middleware or individual endpoints.
"""

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_action(
    session: Session,
    user: User | None = None,
    action: str = "",
    resource_type: str | None = None,
    resource_id: str | None = None,
    method: str | None = None,
    path: str | None = None,
    status_code: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    extra: dict | None = None,
) -> AuditLog:
    """Create and persist an audit log entry.

    Uses a fresh session savepoint so audit failures don't roll back
    the caller's transaction. The caller is responsible for committing.
    """
    entry = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        method=method,
        path=path,
        status_code=str(status_code) if status_code else None,
        detail=detail,
        ip_address=ip_address,
        metadata_=extra or {},
    )
    session.add(entry)
    session.flush()
    return entry


def list_audit_logs(
    session: Session,
    user_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Query audit logs with optional filters."""
    from sqlalchemy import select

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    stmt = stmt.limit(limit).offset(offset)
    return list(session.execute(stmt).scalars().all())
