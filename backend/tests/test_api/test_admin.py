"""Admin API tests — Phase 3."""

import asyncio

import pytest

from app.models.ticket import Ticket


@pytest.fixture
def resolved_tickets(db_session):
    tickets_data = [
        {
            "title": "Login error: invalid credentials",
            "description": "User cannot login due to authentication failure",
            "status": "resolved",
            "priority": "high",
        },
        {
            "title": "Login error: session timeout",
            "description": "User session expires too quickly",
            "status": "closed",
            "priority": "medium",
        },
        {
            "title": "Database connection timeout",
            "description": "Database pool exhausted under load",
            "status": "resolved",
            "priority": "critical",
        },
    ]
    tickets = []
    for data in tickets_data:
        t = Ticket(**data)
        db_session.add(t)
        db_session.flush()
        tickets.append(t)
    db_session.commit()
    return tickets


class TestAdminQuality:
    def test_quality_evaluate(self, client):
        async def run():
            resp = await client.post(
                "/api/v1/admin/quality/evaluate",
                json={
                    "query": "How do I reset my password?",
                    "response": "You can reset your password by clicking the 'Forgot Password' link on the login page.",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "relevance" in data
            assert "accuracy" in data
            assert "completeness" in data
            assert "clarity" in data
            assert "overall" in data

        asyncio.run(run())

    def test_quality_evaluate_batch(self, client):
        async def run():
            resp = await client.post(
                "/api/v1/admin/quality/evaluate-batch",
                json={
                    "responses": [
                        {
                            "query": "What is SLA?",
                            "response": "SLA stands for Service Level Agreement.",
                        },
                        {
                            "query": "How to contact support?",
                            "response": "Email support@example.com or call 1-800-XXX.",
                        },
                    ]
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) == 2
            for item in data:
                assert "relevance" in item
                assert "overall" in item

        asyncio.run(run())

    def test_quality_evaluate_unauthorized(self, unauth_client, db_session):
        from app.services.auth import create_access_token

        token = create_access_token({"sub": "nonexistent", "role": "l1_engineer"})

        async def run():
            resp = await unauth_client.post(
                "/api/v1/admin/quality/evaluate",
                json={"query": "test", "response": "test"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401

        asyncio.run(run())


class TestAdminKnowledge:
    def test_discover_patterns(self, client, resolved_tickets):
        async def run():
            resp = await client.post(
                "/api/v1/admin/knowledge/discover",
                params={"min_tickets": 2},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) > 0
            for item in data:
                assert "pattern" in item
                assert "severity" in item

        asyncio.run(run())

    def test_discover_patterns_unauthorized(self, unauth_client, db_session):
        from app.services.auth import create_access_token

        token = create_access_token({"sub": "nonexistent", "role": "l1_engineer"})

        async def run():
            resp = await unauth_client.post(
                "/api/v1/admin/knowledge/discover",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401

        asyncio.run(run())


class TestAdminStats:
    def test_stats(self, client, db_session, resolved_tickets):
        from app.models.conversation import Conversation, Message
        from app.models.knowledge import KnowledgeDocument

        conv = Conversation(title="Test conversation")
        db_session.add(conv)
        db_session.flush()

        msg = Message(
            conversation_id=conv.id,
            role="user",
            content="Hello",
        )
        db_session.add(msg)
        db_session.flush()

        doc = KnowledgeDocument(
            title="Test doc",
            content="Test content",
        )
        db_session.add(doc)
        db_session.commit()

        async def run():
            resp = await client.get("/api/v1/admin/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert "total_conversations" in data
            assert "total_messages" in data
            assert "total_documents" in data
            assert "total_tickets" in data
            assert "tickets_by_status" in data
            assert "users_by_role" in data
            assert data["total_conversations"] >= 1
            assert data["total_messages"] >= 1
            assert data["total_documents"] >= 1
            assert data["total_tickets"] >= 3

        asyncio.run(run())

    def test_stats_unauthorized(self, unauth_client, db_session):
        from app.services.auth import create_access_token

        token = create_access_token({"sub": "nonexistent", "role": "l1_engineer"})

        async def run():
            resp = await unauth_client.get(
                "/api/v1/admin/stats",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401

        asyncio.run(run())
