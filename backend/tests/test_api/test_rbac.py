"""RBAC + User management API tests — Phase 2 Task 2.3 + 2.4."""

import asyncio

from app.models.user import User
from app.services.auth import create_access_token, hash_password


def _make_user(db_session, email, role):
    user = User(
        email=email,
        name=role.title(),
        password_hash=hash_password("pass123"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _auth_header(user):
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


class TestRBAC:
    def test_admin_can_list_users(self, unauth_client, db_session):
        admin = _make_user(db_session, "admin@example.com", "admin")
        _make_user(db_session, "user1@example.com", "l1_engineer")

        async def run():
            resp = await unauth_client.get(
                "/api/v1/auth/users", headers=_auth_header(admin)
            )
            assert resp.status_code == 200
            assert len(resp.json()) >= 2

        asyncio.run(run())

    def test_manager_can_list_users(self, unauth_client, db_session):
        manager = _make_user(db_session, "manager@example.com", "manager")

        async def run():
            resp = await unauth_client.get(
                "/api/v1/auth/users", headers=_auth_header(manager)
            )
            assert resp.status_code == 200

        asyncio.run(run())

    def test_l1_engineer_cannot_list_users(self, unauth_client, db_session):
        eng = _make_user(db_session, "eng@example.com", "l1_engineer")

        async def run():
            resp = await unauth_client.get(
                "/api/v1/auth/users", headers=_auth_header(eng)
            )
            assert resp.status_code == 403

        asyncio.run(run())

    def test_admin_can_create_user(self, unauth_client, db_session):
        admin = _make_user(db_session, "admin@example.com", "admin")

        async def run():
            resp = await unauth_client.post(
                "/api/v1/auth/users",
                headers=_auth_header(admin),
                json={
                    "email": "newuser@example.com",
                    "name": "New User",
                    "password": "newpass123",
                    "role": "l1_engineer",
                },
            )
            assert resp.status_code == 201
            assert resp.json()["email"] == "newuser@example.com"

        asyncio.run(run())

    def test_l1_engineer_cannot_create_user(self, unauth_client, db_session):
        eng = _make_user(db_session, "eng@example.com", "l1_engineer")

        async def run():
            resp = await unauth_client.post(
                "/api/v1/auth/users",
                headers=_auth_header(eng),
                json={
                    "email": "newuser@example.com",
                    "name": "New User",
                    "password": "newpass123",
                },
            )
            assert resp.status_code == 403

        asyncio.run(run())

    def test_duplicate_email_rejected(self, unauth_client, db_session):
        admin = _make_user(db_session, "admin@example.com", "admin")

        async def run():
            resp = await unauth_client.post(
                "/api/v1/auth/users",
                headers=_auth_header(admin),
                json={
                    "email": "admin@example.com",
                    "name": "Dup",
                    "password": "pass123",
                },
            )
            assert resp.status_code == 400

        asyncio.run(run())


class TestUserManagement:
    def test_update_user_role(self, unauth_client, db_session):
        admin = _make_user(db_session, "admin@example.com", "admin")
        target = _make_user(db_session, "target@example.com", "l1_engineer")

        async def run():
            resp = await unauth_client.patch(
                f"/api/v1/auth/users/{target.id}",
                headers=_auth_header(admin),
                json={"role": "l2_engineer"},
            )
            assert resp.status_code == 200
            assert resp.json()["role"] == "l2_engineer"

        asyncio.run(run())

    def test_deactivate_user(self, unauth_client, db_session):
        admin = _make_user(db_session, "admin@example.com", "admin")
        target = _make_user(db_session, "target@example.com", "l1_engineer")

        async def run():
            resp = await unauth_client.patch(
                f"/api/v1/auth/users/{target.id}",
                headers=_auth_header(admin),
                json={"is_active": False},
            )
            assert resp.status_code == 200
            assert resp.json()["is_active"] is False

        asyncio.run(run())

    def test_change_password_correct(self, unauth_client, db_session):
        user = _make_user(db_session, "user@example.com", "l1_engineer")

        async def run():
            resp = await unauth_client.post(
                "/api/v1/auth/change-password",
                headers=_auth_header(user),
                json={"old_password": "pass123", "new_password": "newpass456"},
            )
            assert resp.status_code == 204

        asyncio.run(run())

    def test_change_password_wrong_old(self, unauth_client, db_session):
        user = _make_user(db_session, "user@example.com", "l1_engineer")

        async def run():
            resp = await unauth_client.post(
                "/api/v1/auth/change-password",
                headers=_auth_header(user),
                json={"old_password": "wrongpass", "new_password": "newpass456"},
            )
            assert resp.status_code == 400

        asyncio.run(run())

    def test_update_nonexistent_user_404(self, unauth_client, db_session):
        admin = _make_user(db_session, "admin@example.com", "admin")

        async def run():
            resp = await unauth_client.patch(
                "/api/v1/auth/users/nonexistent-id",
                headers=_auth_header(admin),
                json={"role": "manager"},
            )
            assert resp.status_code == 404

        asyncio.run(run())
