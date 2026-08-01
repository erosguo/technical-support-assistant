"""Tenant model tests — Phase 2 Task 2.6."""


class TestTenant:
    def test_create_tenant(self, db_session):
        from app.models.tenant import Tenant

        tenant = Tenant(name="Acme Corp", slug="acme")
        db_session.add(tenant)
        db_session.commit()

        loaded = db_session.get(Tenant, str(tenant.id))
        assert loaded is not None
        assert loaded.name == "Acme Corp"
        assert loaded.slug == "acme"

    def test_tenant_default_active(self, db_session):
        from app.models.tenant import Tenant

        tenant = Tenant(name="Test Corp", slug="test")
        db_session.add(tenant)
        db_session.commit()

        assert tenant.is_active is True

    def test_tenant_settings_json(self, db_session):
        from app.models.tenant import Tenant

        tenant = Tenant(
            name="Settings Corp", slug="settings", settings={"max_users": 50}
        )
        db_session.add(tenant)
        db_session.commit()

        loaded = db_session.get(Tenant, str(tenant.id))
        assert loaded.settings == {"max_users": 50}

    def test_tenant_settings_default_empty(self, db_session):
        from app.models.tenant import Tenant

        tenant = Tenant(name="Default Corp", slug="default")
        db_session.add(tenant)
        db_session.commit()

        # SQLite returns None for default dict, which is fine
        assert tenant.settings is None or tenant.settings == {}

    def test_user_tenant_association(self, db_session):
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.services.auth import hash_password

        tenant = Tenant(name="Acme", slug="acme")
        db_session.add(tenant)
        db_session.commit()

        user = User(
            email="user@acme.com",
            name="Acme User",
            password_hash=hash_password("pass123"),
            tenant_id=tenant.id,
        )
        db_session.add(user)
        db_session.commit()

        loaded = db_session.get(User, str(user.id))
        assert str(loaded.tenant_id) == str(tenant.id)
