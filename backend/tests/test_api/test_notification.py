"""Notification API tests — Phase 3."""

import asyncio

import pytest


@pytest.fixture
def manager_user(db_session):
    from app.models.user import User
    from app.services.auth import hash_password

    user = User(
        email="manager@example.com",
        name="Manager",
        password_hash=hash_password("pass123"),
        role="manager",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def manager_client(db_session, manager_user):
    import asyncio
    from httpx import ASGITransport, AsyncClient
    from app.db.session import get_session
    from app.main import app
    from app.services.auth import get_current_user

    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = lambda: manager_user
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    asyncio.run(client.aclose())
    app.dependency_overrides.clear()


class TestNotification:
    def test_send_feishu(self, client):
        async def run():
            resp = await client.post(
                "/api/v1/notification/send",
                json={
                    "provider": "FEISHU",
                    "webhook_url": "https://feishu.example.com/webhook",
                    "title": "Test Alert",
                    "content": "This is a test notification",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["provider"] == "FEISHU"
            assert "sent_at" in data

        asyncio.run(run())

    def test_send_slack(self, client):
        async def run():
            resp = await client.post(
                "/api/v1/notification/send",
                json={
                    "provider": "SLACK",
                    "webhook_url": "https://hooks.slack.com/test",
                    "title": "Slack Alert",
                    "content": "This is a slack test",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["provider"] == "SLACK"

        asyncio.run(run())

    def test_escalation(self, client):
        async def run():
            resp = await client.post(
                "/api/v1/notification/escalation",
                json={
                    "provider": "FEISHU",
                    "webhook_url": "https://feishu.example.com/webhook",
                    "ticket_title": "Critical System Down",
                    "ticket_description": "Production system is not responding",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["provider"] == "FEISHU"
            assert "sent_at" in data

        asyncio.run(run())

    def test_escalation_manager(self, manager_client):
        async def run():
            resp = await manager_client.post(
                "/api/v1/notification/escalation",
                json={
                    "provider": "DINGTALK",
                    "webhook_url": "https://dingtalk.example.com/webhook",
                    "ticket_title": "Manager Escalation",
                    "ticket_description": "Manager level escalation test",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True

        asyncio.run(run())

    def test_escalation_unauthorized(self, unauth_client, db_session):
        from app.services.auth import create_access_token

        token = create_access_token({"sub": "nonexistent", "role": "l1_engineer"})

        async def run():
            resp = await unauth_client.post(
                "/api/v1/notification/escalation",
                json={
                    "provider": "FEISHU",
                    "webhook_url": "https://feishu.example.com/webhook",
                    "ticket_title": "Test",
                    "ticket_description": "Test",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401

        asyncio.run(run())
