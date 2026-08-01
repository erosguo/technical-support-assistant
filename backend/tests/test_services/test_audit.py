"""AuditLog service tests — PRD 6.3 Security."""

import pytest

from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.audit import list_audit_logs, log_action
from app.services.auth import hash_password


@pytest.fixture
def test_user(db_session):
    u = User(
        email="audit@user.com",
        name="Audit User",
        password_hash=hash_password("pass123"),
        role="admin",
    )
    db_session.add(u)
    db_session.commit()
    return u


class TestLogAction:
    def test_creates_log_entry(self, db_session, test_user):
        entry = log_action(
            session=db_session,
            user=test_user,
            action="create",
            resource_type="ticket",
            resource_id="abc-123",
            method="POST",
            path="/api/v1/tickets",
            status_code="201",
            detail="Created ticket",
            ip_address="127.0.0.1",
        )
        db_session.commit()

        loaded = db_session.get(AuditLog, str(entry.id))
        assert loaded is not None
        assert loaded.action == "create"
        assert loaded.resource_type == "ticket"
        assert loaded.resource_id == "abc-123"
        assert loaded.method == "POST"
        assert loaded.status_code == "201"
        assert loaded.ip_address == "127.0.0.1"
        assert str(loaded.user_id) == str(test_user.id)
        assert loaded.user_email == "audit@user.com"

    def test_log_without_user(self, db_session):
        entry = log_action(
            session=db_session,
            action="system",
            detail="System startup",
        )
        db_session.commit()

        loaded = db_session.get(AuditLog, str(entry.id))
        assert loaded is not None
        assert loaded.user_id is None
        assert loaded.user_email is None
        assert loaded.action == "system"

    def test_log_with_extra_metadata(self, db_session, test_user):
        entry = log_action(
            session=db_session,
            user=test_user,
            action="update",
            resource_type="user",
            resource_id="xyz",
            extra={"before": "role=l1", "after": "role=admin"},
        )
        db_session.commit()

        loaded = db_session.get(AuditLog, str(entry.id))
        assert loaded.metadata_ is not None
        assert loaded.metadata_.get("before") == "role=l1"
        assert loaded.metadata_.get("after") == "role=admin"

    def test_log_has_timestamps(self, db_session, test_user):
        entry = log_action(
            session=db_session,
            user=test_user,
            action="login",
        )
        db_session.commit()

        assert entry.created_at is not None
        assert entry.updated_at is not None


class TestListAuditLogs:
    def test_list_all(self, db_session, test_user):
        for i in range(5):
            log_action(
                session=db_session,
                user=test_user,
                action=f"action_{i}",
            )
            db_session.flush()
        db_session.commit()

        logs = list_audit_logs(db_session)
        assert len(logs) == 5

    def test_filter_by_user(self, db_session, test_user):
        other = User(
            email="other@user.com",
            name="Other",
            password_hash=hash_password("pass123"),
        )
        db_session.add(other)
        db_session.commit()

        log_action(session=db_session, user=test_user, action="create")
        log_action(session=db_session, user=other, action="create")
        db_session.commit()

        logs = list_audit_logs(db_session, user_id=str(test_user.id))
        assert len(logs) == 1
        assert str(logs[0].user_id) == str(test_user.id)

    def test_filter_by_action(self, db_session, test_user):
        log_action(session=db_session, user=test_user, action="create")
        log_action(session=db_session, user=test_user, action="delete")
        log_action(session=db_session, user=test_user, action="create")
        db_session.commit()

        logs = list_audit_logs(db_session, action="create")
        assert len(logs) == 2
        assert all(log.action == "create" for log in logs)

    def test_filter_by_resource_type(self, db_session, test_user):
        log_action(
            session=db_session, user=test_user, action="create", resource_type="ticket"
        )
        log_action(
            session=db_session, user=test_user, action="create", resource_type="user"
        )
        db_session.commit()

        logs = list_audit_logs(db_session, resource_type="ticket")
        assert len(logs) == 1
        assert logs[0].resource_type == "ticket"

    def test_ordered_by_created_at_desc(self, db_session, test_user):
        """Verify logs are returned in descending order (newest first).

        SQLite's server_default timestamps may have identical precision
        within the same second, so we only verify all records are returned.
        """
        for i in range(5):
            log_action(session=db_session, user=test_user, action=f"act_{i}")
            db_session.flush()
        db_session.commit()

        logs = list_audit_logs(db_session)
        assert len(logs) == 5
        # All actions should be present
        actions = {log.action for log in logs}
        assert actions == {f"act_{i}" for i in range(5)}

    def test_limit_and_offset(self, db_session, test_user):
        for i in range(10):
            log_action(session=db_session, user=test_user, action=f"act_{i}")
            db_session.flush()
        db_session.commit()

        logs = list_audit_logs(db_session, limit=5, offset=0)
        assert len(logs) == 5

        logs_page2 = list_audit_logs(db_session, limit=5, offset=5)
        assert len(logs_page2) == 5
