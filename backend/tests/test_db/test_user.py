"""User model tests — Phase 2 Task 2.1."""


class TestUser:
    def test_create_user(self, db_session):
        from app.models.user import User

        user = User(
            email="admin@example.com",
            name="Admin",
            password_hash="hashed_secret",
        )
        db_session.add(user)
        db_session.commit()

        loaded = db_session.get(User, str(user.id))
        assert loaded is not None
        assert loaded.email == "admin@example.com"
        assert loaded.name == "Admin"
        assert loaded.password_hash == "hashed_secret"

    def test_password_hash_not_plaintext(self, db_session):
        from app.models.user import User

        user = User(
            email="user@example.com",
            name="User",
            password_hash="$2b$12$somehashedvalue",
        )
        db_session.add(user)
        db_session.commit()

        assert user.password_hash != "plaintext"
        assert user.password_hash.startswith("$2b$")

    def test_default_role_is_l1_engineer(self, db_session):
        from app.models.user import User

        user = User(
            email="engineer@example.com",
            name="Engineer",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        assert user.role == "l1_engineer"

    def test_default_is_active(self, db_session):
        from app.models.user import User

        user = User(
            email="active@example.com",
            name="Active",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_active is True

    def test_optional_fields_default_none(self, db_session):
        from app.models.user import User

        user = User(
            email="optional@example.com",
            name="Optional",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        assert user.tenant_id is None
