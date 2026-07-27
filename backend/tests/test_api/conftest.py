import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from app.db.session import get_session
from app.main import app


@pytest.fixture
def client(db_session):
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    asyncio.run(client.aclose())
    app.dependency_overrides.clear()
