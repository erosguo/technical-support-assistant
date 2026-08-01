"""Core test fixtures. Uses sync SQLAlchemy with SQLite for test isolation."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.db.base import Base
import app.models  # noqa: F401 — register all models with Base.metadata
from tests.mock_providers import MockLLMProvider

TEST_DB_DSN = "sqlite:///./test.db"
test_engine = create_engine(
    TEST_DB_DSN, echo=False, connect_args={"check_same_thread": False}
)


@event.listens_for(test_engine, "connect")
def _enable_fk(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


TestSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Session:
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    return MockLLMProvider(
        responses={
            "你好": "你好！我是技术支持助手，有什么可以帮助你的？",
            "default": "这是一个模拟回复，用于测试场景。",
        }
    )
