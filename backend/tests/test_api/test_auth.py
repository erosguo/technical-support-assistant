"""Auth API tests — Phase 2 Task 2.2."""

import pytest
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("testpass123"),
        role="l1_engineer",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestAuthAPI:
    def test_login_success(self, client, db_session, test_user):
        import asyncio

        async def run():
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "testpass123"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

        asyncio.run(run())

    def test_login_wrong_password(self, client, db_session, test_user):
        import asyncio

        async def run():
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrongpass"},
            )
            assert resp.status_code == 401

        asyncio.run(run())

    def test_login_nonexistent_user(self, client, db_session):
        import asyncio

        async def run():
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@example.com", "password": "pass"},
            )
            assert resp.status_code == 401

        asyncio.run(run())

    def test_me_with_valid_token(self, client, db_session, test_user):
        import asyncio

        from app.services.auth import create_access_token

        token = create_access_token({"sub": str(test_user.id)})

        async def run():
            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["email"] == "test@example.com"
            assert data["name"] == "Test User"
            assert data["role"] == "l1_engineer"

        asyncio.run(run())

    def test_me_without_token(self, client, db_session):
        import asyncio

        async def run():
            resp = await client.get("/api/v1/auth/me")
            assert resp.status_code == 401

        asyncio.run(run())

    def test_me_with_invalid_token(self, client, db_session):
        import asyncio

        async def run():
            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid.token.here"},
            )
            assert resp.status_code == 401

        asyncio.run(run())
