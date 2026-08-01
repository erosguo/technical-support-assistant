"""Diagnosis flow API tests — Phase 2 Task 2.7."""

import asyncio

from app.models.user import User
from app.services.auth import create_access_token, hash_password


def _make_user(db_session, role="admin"):
    user = User(
        email=f"{role}@example.com",
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


class TestDiagnosisFlowAPI:
    def test_create_flow(self, client, db_session):
        admin = _make_user(db_session)

        async def run():
            resp = await client.post(
                "/api/v1/diagnosis/flows",
                headers=_auth_header(admin),
                json={
                    "name": "SSL 诊断",
                    "description": "SSL 证书问题",
                    "steps": [{"id": "s1", "title": "检查证书"}],
                },
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["name"] == "SSL 诊断"
            assert len(data["steps"]) == 1
            assert data["version"] == 1

        asyncio.run(run())

    def test_list_flows(self, client, db_session):
        admin = _make_user(db_session)

        async def run():
            # Create two flows
            for i in range(2):
                await client.post(
                    "/api/v1/diagnosis/flows",
                    headers=_auth_header(admin),
                    json={
                        "name": f"Flow {i}",
                        "steps": [{"id": "s1", "title": "Step"}],
                    },
                )
            resp = await client.get(
                "/api/v1/diagnosis/flows", headers=_auth_header(admin)
            )
            assert resp.status_code == 200
            assert len(resp.json()) >= 2

        asyncio.run(run())

    def test_get_flow(self, client, db_session):
        admin = _make_user(db_session)

        async def run():
            create = await client.post(
                "/api/v1/diagnosis/flows",
                headers=_auth_header(admin),
                json={"name": "Get Test", "steps": [{"id": "s1", "title": "Step"}]},
            )
            flow_id = create.json()["id"]
            resp = await client.get(
                f"/api/v1/diagnosis/flows/{flow_id}", headers=_auth_header(admin)
            )
            assert resp.status_code == 200
            assert resp.json()["name"] == "Get Test"

        asyncio.run(run())

    def test_update_flow_increments_version(self, client, db_session):
        admin = _make_user(db_session)

        async def run():
            create = await client.post(
                "/api/v1/diagnosis/flows",
                headers=_auth_header(admin),
                json={"name": "Original", "steps": [{"id": "s1", "title": "Step"}]},
            )
            flow_id = create.json()["id"]
            resp = await client.patch(
                f"/api/v1/diagnosis/flows/{flow_id}",
                headers=_auth_header(admin),
                json={
                    "steps": [
                        {"id": "s1", "title": "Updated Step"},
                        {"id": "s2", "title": "New"},
                    ]
                },
            )
            assert resp.status_code == 200
            assert resp.json()["version"] == 2
            assert len(resp.json()["steps"]) == 2

        asyncio.run(run())

    def test_delete_flow(self, client, db_session):
        admin = _make_user(db_session)

        async def run():
            create = await client.post(
                "/api/v1/diagnosis/flows",
                headers=_auth_header(admin),
                json={"name": "Delete Me", "steps": [{"id": "s1", "title": "Step"}]},
            )
            flow_id = create.json()["id"]
            resp = await client.delete(
                f"/api/v1/diagnosis/flows/{flow_id}", headers=_auth_header(admin)
            )
            assert resp.status_code == 204
            # Verify deleted
            get_resp = await client.get(
                f"/api/v1/diagnosis/flows/{flow_id}", headers=_auth_header(admin)
            )
            assert get_resp.status_code == 404

        asyncio.run(run())

    def test_activate_flow(self, client, db_session):
        admin = _make_user(db_session)

        async def run():
            # Create two flows
            f1 = await client.post(
                "/api/v1/diagnosis/flows",
                headers=_auth_header(admin),
                json={"name": "Flow 1", "steps": [{"id": "s1", "title": "Step"}]},
            )
            f2 = await client.post(
                "/api/v1/diagnosis/flows",
                headers=_auth_header(admin),
                json={"name": "Flow 2", "steps": [{"id": "s1", "title": "Step"}]},
            )
            # Activate flow 2
            resp = await client.post(
                f"/api/v1/diagnosis/flows/{f2.json()['id']}/activate",
                headers=_auth_header(admin),
            )
            assert resp.status_code == 200
            assert resp.json()["is_active"] is True
            # Flow 1 should be deactivated
            f1_resp = await client.get(
                f"/api/v1/diagnosis/flows/{f1.json()['id']}",
                headers=_auth_header(admin),
            )
            assert f1_resp.json()["is_active"] is False

        asyncio.run(run())

    def test_get_nonexistent_flow_404(self, client, db_session):
        admin = _make_user(db_session)

        async def run():
            resp = await client.get(
                "/api/v1/diagnosis/flows/nonexistent",
                headers=_auth_header(admin),
            )
            assert resp.status_code == 404

        asyncio.run(run())
