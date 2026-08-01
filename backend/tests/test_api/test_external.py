"""External ticket API tests — Phase 3."""

import asyncio

import pytest

from app.models.ticket import Ticket


@pytest.fixture
def sample_ticket(db_session):
    ticket = Ticket(
        title="Test ticket for external sync",
        description="This is a test ticket description",
        status="open",
        priority="high",
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


@pytest.fixture
def l2_user(db_session):
    from app.models.user import User
    from app.services.auth import hash_password

    user = User(
        email="l2@example.com",
        name="L2 Engineer",
        password_hash=hash_password("pass123"),
        role="l2_engineer",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def l2_client(db_session, l2_user):
    import asyncio
    from httpx import ASGITransport, AsyncClient
    from app.db.session import get_session
    from app.main import app
    from app.services.auth import get_current_user

    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = lambda: l2_user
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    asyncio.run(client.aclose())
    app.dependency_overrides.clear()


class TestExternalTickets:
    def test_sync_jira(self, client, sample_ticket):
        async def run():
            resp = await client.post(
                "/api/v1/external/tickets/sync",
                json={"ticket_id": str(sample_ticket.id), "provider": "JIRA"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "JIRA"
            assert data["status"] == "synced"
            assert "external_id" in data

        asyncio.run(run())

    def test_sync_zendesk(self, client, sample_ticket):
        async def run():
            resp = await client.post(
                "/api/v1/external/tickets/sync",
                json={"ticket_id": str(sample_ticket.id), "provider": "ZENDESK"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "ZENDESK"
            assert data["status"] == "synced"

        asyncio.run(run())

    def test_get_config_admin(self, client):
        async def run():
            resp = await client.get("/api/v1/external/tickets/config/JIRA")
            assert resp.status_code == 200
            data = resp.json()
            assert "base_url" in data
            assert data["base_url"] == "https://example.atlassian.net"

        asyncio.run(run())

    def test_sync_unauthorized_role(self, unauth_client, db_session, sample_ticket):
        from app.services.auth import create_access_token

        token = create_access_token({"sub": "nonexistent", "role": "l1_engineer"})

        async def run():
            resp = await unauth_client.post(
                "/api/v1/external/tickets/sync",
                json={"ticket_id": str(sample_ticket.id), "provider": "JIRA"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401

        asyncio.run(run())

    def test_sync_invalid_ticket(self, client):
        async def run():
            resp = await client.post(
                "/api/v1/external/tickets/sync",
                json={"ticket_id": "nonexistent-id", "provider": "JIRA"},
            )
            assert resp.status_code == 404

        asyncio.run(run())

    def test_get_config_unauthorized(self, unauth_client, db_session):
        from app.services.auth import create_access_token

        token = create_access_token({"sub": "nonexistent", "role": "l2_engineer"})

        async def run():
            resp = await unauth_client.get(
                "/api/v1/external/tickets/config/JIRA",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401

        asyncio.run(run())
