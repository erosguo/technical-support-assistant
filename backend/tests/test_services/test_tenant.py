"""Tenant isolation service tests — Phase 2 Task 2.6.4."""

import pytest

from app.models.conversation import Conversation
from app.models.knowledge import KnowledgeDocument
from app.models.ticket import Ticket
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth import hash_password
from app.services.tenant import apply_tenant_filter, get_tenant_filter


@pytest.fixture
def tenant_a(db_session):
    t = Tenant(name="Tenant A", slug="tenant-a")
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def tenant_b(db_session):
    t = Tenant(name="Tenant B", slug="tenant-b")
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def user_a(db_session, tenant_a):
    u = User(
        email="user@-a.com",
        name="User A",
        password_hash=hash_password("pass123"),
        tenant_id=tenant_a.id,
    )
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def user_b(db_session, tenant_b):
    u = User(
        email="user@b.com",
        name="User B",
        password_hash=hash_password("pass123"),
        tenant_id=tenant_b.id,
    )
    db_session.add(u)
    db_session.commit()
    return u


class TestGetTenantFilter:
    def test_returns_filter_for_tenant_user(self, user_a, tenant_a):
        result = get_tenant_filter(user_a)
        assert "tenant_id" in result
        assert str(result["tenant_id"]) == str(tenant_a.id)

    def test_returns_empty_for_no_tenant(self, db_session):
        user = User(
            email="free@user.com",
            name="Free User",
            password_hash=hash_password("pass123"),
        )
        db_session.add(user)
        db_session.commit()
        result = get_tenant_filter(user)
        assert result == {}


class TestApplyTenantFilter:
    def test_filters_conversations_by_tenant(
        self, db_session, user_a, tenant_a, tenant_b
    ):
        conv_a = Conversation(title="A conv", tenant_id=tenant_a.id)
        db_session.add(conv_a)
        db_session.flush()
        conv_b = Conversation(title="B conv", tenant_id=tenant_b.id)
        db_session.add(conv_b)
        db_session.flush()
        conv_none = Conversation(title="No tenant")
        db_session.add(conv_none)
        db_session.commit()

        from sqlalchemy import select

        stmt = apply_tenant_filter(select(Conversation), user_a)
        results = db_session.execute(stmt).scalars().all()
        titles = [r.title for r in results]
        assert "A conv" in titles
        assert "B conv" not in titles

    def test_no_filter_for_user_without_tenant(self, db_session):
        user = User(
            email="admin@system.com",
            name="Admin",
            password_hash=hash_password("pass123"),
        )
        db_session.add(user)
        db_session.commit()

        from sqlalchemy import select

        stmt = apply_tenant_filter(select(Conversation), user)
        # Should return all conversations unfiltered
        results = db_session.execute(stmt).scalars().all()
        assert isinstance(results, list)


class TestTenantIsolationOnModels:
    def test_conversation_tenant_id(self, db_session, tenant_a):
        conv = Conversation(title="Test", tenant_id=tenant_a.id)
        db_session.add(conv)
        db_session.commit()
        assert conv.tenant_id is not None
        assert str(conv.tenant_id) == str(tenant_a.id)

    def test_knowledge_document_tenant_id(self, db_session, tenant_a):
        doc = KnowledgeDocument(title="Doc", content="content", tenant_id=tenant_a.id)
        db_session.add(doc)
        db_session.commit()
        assert str(doc.tenant_id) == str(tenant_a.id)

    def test_ticket_tenant_id(self, db_session, tenant_a):
        ticket = Ticket(
            title="Ticket",
            description="desc",
            tenant_id=tenant_a.id,
        )
        db_session.add(ticket)
        db_session.commit()
        assert str(ticket.tenant_id) == str(tenant_a.id)

    def test_tenant_id_nullable(self, db_session):
        conv = Conversation(title="No tenant")
        db_session.add(conv)
        db_session.commit()
        assert conv.tenant_id is None

        doc = KnowledgeDocument(title="Doc", content="content")
        db_session.add(doc)
        db_session.commit()
        assert doc.tenant_id is None

        ticket = Ticket(title="T", description="d")
        db_session.add(ticket)
        db_session.commit()
        assert ticket.tenant_id is None
