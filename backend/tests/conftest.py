"""Core test fixtures. Uses sync SQLAlchemy with SQLite for test isolation."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.base import Base
from tests.mock_providers import MockLLMProvider

TEST_DB_DSN = "sqlite:///./test.db"
test_engine = create_engine(TEST_DB_DSN, echo=False)
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
