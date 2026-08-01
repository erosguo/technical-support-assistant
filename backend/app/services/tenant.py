"""Tenant isolation utilities — Phase 2 Task 2.6.4.

Provides helper functions to apply tenant-scoped filtering to queries,
ensuring data isolation between organizations.
"""

from sqlalchemy.orm import Session

from app.models.user import User


def get_tenant_filter(user: User) -> dict:
    """Return the tenant filter dict for the given user.

    If the user has no tenant_id, returns an empty dict (no filtering),
    which is appropriate for super-admin / system-level access.
    """
    if user and user.tenant_id:
        return {"tenant_id": user.tenant_id}
    return {}


def apply_tenant_filter(query, user: User):
    """Apply tenant filtering to a SQLAlchemy query.

    Usage::

        stmt = apply_tenant_filter(select(Conversation), current_user)
        results = session.execute(stmt).scalars().all()

    If the user has no tenant_id, the query is returned unmodified.
    """
    if user and user.tenant_id:
        # Inspect the query's primary entity to check for tenant_id column
        entity = query.column_descriptions[0]["entity"]
        if entity is not None and hasattr(entity, "tenant_id"):
            return query.where(entity.tenant_id == user.tenant_id)
    return query


def get_user_tenant_id(session: Session, user: User):
    """Return the tenant_id for the given user, or None."""
    if user and user.tenant_id:
        return user.tenant_id
    return None
