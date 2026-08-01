import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from app.db.session import get_session
from app.main import app
from app.models.user import User
from app.services.auth import get_current_user, hash_password


@pytest.fixture
def default_user(db_session):
    """Create a default admin user for authenticated tests."""
    user = db_session.query(User).filter(User.email == "test-admin@example.com").first()
    if not user:
        user = User(
            email="test-admin@example.com",
            name="Test Admin",
            password_hash=hash_password("pass123"),
            role="admin",
        )
        db_session.add(user)
        db_session.commit()
    return user


@pytest.fixture
def client(db_session, default_user):
    """Authenticated client — overrides get_current_user to return admin."""

    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = lambda: default_user
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    asyncio.run(client.aclose())
    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client(db_session):
    """Unauthenticated client — does NOT override get_current_user.
    Use for tests that need real JWT auth (login, RBAC, etc.).
    """

    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    asyncio.run(client.aclose())
    app.dependency_overrides.clear()
