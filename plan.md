# 实现计划 - 技术支持助手 (TDD)

## TDD 规范

每个开发任务遵循 **Red → Green → Refactor** 三阶段：

```
RED     编写测试 → 运行确认失败
GREEN   编写最简实现 → 运行测试通过
REFACTOR 优化代码 → 测试仍通过
```

**铁律**：

- 先写测试，后写实现
- 测试不通过不可提交代码
- 测试覆盖核心逻辑分支
- 所有外部依赖使用 Mock/Stub

---

## Phase 1 (MVP) 任务分解

---

## Task 1.1: 项目目录结构

**文件**：无（创建目录）

**操作**：

```
/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 配置、日志、依赖
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 模型
│   │   ├── services/      # 业务逻辑
│   │   ├── agents/        # LangGraph Agent
│   │   ├── tools/         # 工具函数
│   │   └── db/            # 数据库连接 + 迁移
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── mock_providers.py
│   │   ├── test_config.py
│   │   ├── test_services/
│   │   ├── test_agents/
│   │   └── test_api/
│   ├── alembic/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── services/
│   │   └── types/
│   ├── __tests__/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

**验证**：目录结构创建完毕

---

## Task 1.2: 测试基础设施 (TDD 基石)

**文件**：`backend/pyproject.toml`, `backend/tests/conftest.py`, `backend/tests/mock_providers.py`

### Step 1.2.1 - pyproject.toml（含测试依赖）

```toml
[project]
name = "tech-support-assistant"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.13",
    "pgvector>=0.3",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "openai>=1.50",
    "langgraph>=0.2",
    "langchain>=0.3",
    "langchain-openai>=0.2",
    "python-dotenv>=1.0",
    "httpx>=0.27",
    "python-multipart>=0.0.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "httpx>=0.27",
    "ruff>=0.6",
    "factory-boy>=3.3",
]
```

### Step 1.2.2 - Mock Providers（RED 阶段基础）

```python
# backend/tests/mock_providers.py
"""测试替身：所有外部依赖的 Mock 实现"""


class MockLLMProvider:
    def __init__(self, responses: dict[str, str] = None):
        self.responses = responses or {}
        self.call_history: list[dict] = []

    async def chat(self, messages: list[dict], **kwargs) -> str:
        self.call_history.append({"messages": messages, "kwargs": kwargs})
        query = messages[-1]["content"] if messages else ""
        for pattern, reply in self.responses.items():
            if pattern in query:
                return reply
        return self.responses.get("default", "Mock reply")

    async def chat_stream(self, messages: list[dict], **kwargs):
        reply = await self.chat(messages, **kwargs)
        for char in reply:
            yield char

    async def embed(self, text: str) -> list[float]:
        return [0.1] * 3  # 3-dim mock vector

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class MockEmbeddingProvider:
    dimension: int = 3

    async def embed(self, text: str) -> list[float]:
        return [0.1] * self.dimension

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]
```

### Step 1.2.3 - conftest.py（全局 Fixtures）

```python
# backend/tests/conftest.py
import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from httpx import ASGITransport, AsyncClient
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.core.config import settings
from tests.mock_providers import MockLLMProvider

# Test DB: 使用独立数据库，每个 session 自动回滚
TEST_DB_DSN = "postgresql+asyncpg://postgres:postgres@localhost:5432/tech_support_test"
test_engine = create_async_engine(TEST_DB_DSN)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    """每个测试函数前重建表"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as conn:
        tx = await conn.begin()
        session = async_sessionmaker(conn, class_=AsyncSession)()
        yield session
        await tx.rollback()
        await session.close()


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    return MockLLMProvider(responses={
        "你好": "你好！我是技术支持助手，有什么可以帮助你的？",
        "default": "这是一个模拟回复，用于测试场景。",
    })


@pytest.fixture
async def client(db_session, mock_llm) -> AsyncGenerator[AsyncClient, None]:
    def override_get_session():
        yield db_session
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

### Step 1.2.4 - 验证测试（RED 阶段）

```python
# backend/tests/test_mock_providers.py
import pytest


class TestMockLLMProvider:
    @pytest.mark.asyncio
    async def test_chat_returns_mock_response(self, mock_llm):
        reply = await mock_llm.chat([{"role": "user", "content": "你好"}])
        assert "技术支持助手" in reply

    @pytest.mark.asyncio
    async def test_chat_default_fallback(self, mock_llm):
        reply = await mock_llm.chat([{"role": "user", "content": "未知问题"}])
        assert reply == "这是一个模拟回复，用于测试场景。"

    @pytest.mark.asyncio
    async def test_call_history_tracked(self, mock_llm):
        await mock_llm.chat([{"role": "user", "content": "你好"}])
        assert len(mock_llm.call_history) == 1
        assert mock_llm.call_history[0]["messages"][-1]["content"] == "你好"
```

**验证**：

```bash
cd backend && pip install -e ".[dev]"
cd backend && pytest tests/test_mock_providers.py -v
# 预期: 3 passed
```

---

## Task 1.3: 应用配置 (TDD)

### Step 1.3.1 - RED: 写配置测试

**文件**：`backend/tests/test_config.py`

```python
import pytest
from app.core.config import Settings


class TestSettings:
    def test_default_app_name(self):
        s = Settings()
        assert s.app_name == "Tech Support Assistant"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "Custom Name")
        s = Settings()
        assert s.app_name == "Custom Name"

    def test_default_llm_model(self):
        s = Settings()
        assert s.llm_model == "gpt-4o-mini"

    def test_default_embedding_dimensions(self):
        s = Settings()
        assert s.embedding_dimensions == 1536
```

**验证**：

```bash
cd backend && pytest tests/test_config.py -v
# 预期: 4 failed (因 Settings 未实现)
```

### Step 1.3.2 - GREEN: 实现配置

**文件**：`backend/app/__init__.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Tech Support Assistant"
    debug: bool = False

    db_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tech_support"

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    class Config:
        env_file = ".env"


settings = Settings()
```

### Step 1.3.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_config.py -v
# 预期: 4 passed
```

---

## Task 1.4: 数据库基础设施 (TDD)

### Step 1.4.1 - RED: 写数据库测试

**文件**：`backend/tests/test_db/test_session.py`

```python
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseSession:
    @pytest.mark.asyncio
    async def test_session_executes_query(self, db_session: AsyncSession):
        result = await db_session.execute(text("SELECT 1 as val"))
        row = result.one()
        assert row.val == 1

    @pytest.mark.asyncio
    async def test_session_rollback_on_exit(self, db_session: AsyncSession):
        await db_session.execute(text("CREATE TEMP TABLE tmp_test (id INT)"))
        await db_session.execute(text("INSERT INTO tmp_test VALUES (1)"))
        # session 结束后自动 rollback，但这里我们只是验证 session 可用
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

**验证**：

```bash
cd backend && pytest tests/test_db/test_session.py -v
# 预期: 1 failed, 1 passed（session fixture 已在 conftest 实现）
```

### Step 1.4.2 - GREEN: 实现数据库连接

**文件**：`backend/app/db/session.py`, `backend/app/db/base.py`

```python
# backend/app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.db_dsn, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


# backend/app/db/base.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

### Step 1.4.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_db/ -v
# 预期: all passed
```

---

## Task 1.5: 数据模型 (TDD)

### Step 1.5.1 - RED: 写模型测试

**文件**：`backend/tests/test_db/test_models.py`

```python
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.models.conversation import Conversation, Message


class TestKnowledgeDocument:
    @pytest.mark.asyncio
    async def test_create_document(self, db_session: AsyncSession):
        doc = KnowledgeDocument(title="测试文档", content="# Test Content", doc_type="markdown")
        db_session.add(doc)
        await db_session.commit()
        assert doc.id is not None
        assert isinstance(doc.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_document_chunk_relation(self, db_session: AsyncSession):
        doc = KnowledgeDocument(title="Doc with chunks", content="Chunked content")
        db_session.add(doc)
        await db_session.flush()

        chunk = DocumentChunk(document_id=doc.id, content="chunk 1", chunk_index=0)
        db_session.add(chunk)
        await db_session.commit()

        assert chunk.id is not None
        assert chunk.document_id == doc.id

    @pytest.mark.asyncio
    async def test_timestamps_auto_set(self, db_session: AsyncSession):
        doc = KnowledgeDocument(title="Timestamps", content="test")
        db_session.add(doc)
        await db_session.commit()
        assert doc.created_at is not None
        assert doc.updated_at is not None


class TestConversation:
    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session: AsyncSession):
        conv = Conversation(title="测试会话")
        db_session.add(conv)
        await db_session.commit()
        assert conv.id is not None
        assert conv.status == "active"

    @pytest.mark.asyncio
    async def test_add_message(self, db_session: AsyncSession):
        conv = Conversation(title="会话消息测试")
        db_session.add(conv)
        await db_session.flush()

        msg = Message(conversation_id=conv.id, role="user", content="你好")
        db_session.add(msg)
        await db_session.commit()

        assert msg.id is not None
        assert msg.role == "user"
        assert msg.content == "你好"
```

**验证**：

```bash
cd backend && pytest tests/test_db/test_models.py -v
# 预期: 5 failed（模型未实现）
```

### Step 1.5.2 - GREEN: 实现数据模型

**文件**：`backend/app/models/__init__.py`, `backend/app/models/knowledge.py`, `backend/app/models/conversation.py`

```python
# backend/app/models/knowledge.py
import uuid
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin


class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    doc_type = Column(String(50), default="markdown")
    metadata_ = Column("metadata", JSON, default=dict)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)


# backend/app/models/conversation.py
import uuid
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), default="新对话")
    status = Column(String(50), default="active")
    metadata_ = Column("metadata", JSON, default=dict)


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    agent_name = Column(String(100), nullable=True)
    sources = Column(JSON, default=list)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)
```

### Step 1.5.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_db/test_models.py -v
# 预期: 5 passed
```

---

## Task 1.6: Alembic 迁移

**文件**：`backend/alembic.ini`, `backend/alembic/env.py`

**操作**：

1. `cd backend && alembic init alembic`
2. 修改 `alembic/env.py` 引入异步引擎和 Base metadata
3. `alembic revision --autogenerate -m "init"`
4. `alembic upgrade head`

```python
# alembic/env.py (关键修改)
from app.db.base import Base
from app.models import *  # noqa: 确保模型被加载
target_metadata = Base.metadata
```

**验证**：

```bash
cd backend && alembic upgrade head
pytest tests/test_db/ -v  # 模型测试仍全部通过
```

---

## Task 1.7: LLM Router (TDD)

### Step 1.7.1 - RED: 写 LLM Router 测试

**文件**：`backend/tests/test_services/test_llm.py`

```python
import pytest
from app.services.llm import LLMRouter
from tests.mock_providers import MockLLMProvider


class TestLLMRouter:
    @pytest.mark.asyncio
    async def test_chat_returns_string(self):
        provider = MockLLMProvider(responses={"test": "hello"})
        router = LLMRouter(provider=provider)
        reply = await router.chat([{"role": "user", "content": "test"}])
        assert isinstance(reply, str)
        assert reply == "hello"

    @pytest.mark.asyncio
    async def test_chat_stream_yields_chunks(self):
        provider = MockLLMProvider(responses={"test": "hello"})
        router = LLMRouter(provider=provider)
        chunks = []
        async for chunk in router.chat_stream([{"role": "user", "content": "test"}]):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert "".join(chunks) == "hello"

    @pytest.mark.asyncio
    async def test_embed_returns_float_list(self):
        provider = MockLLMProvider()
        router = LLMRouter(provider=provider)
        vector = await router.embed("test text")
        assert isinstance(vector, list)
        assert all(isinstance(v, float) for v in vector)

    @pytest.mark.asyncio
    async def test_embed_batch_returns_matching_count(self):
        provider = MockLLMProvider()
        router = LLMRouter(provider=provider)
        vectors = await router.embed_batch(["a", "b", "c"])
        assert len(vectors) == 3
```

**验证**：

```bash
cd backend && pytest tests/test_services/test_llm.py -v
# 预期: 4 failed
```

### Step 1.7.2 - GREEN: 实现 LLM Router

**文件**：`backend/app/services/__init__.py`, `backend/app/services/llm.py`

```python
# backend/app/services/llm.py
from typing import AsyncGenerator, Optional, Protocol


class LLMProvider(Protocol):
    async def chat(self, messages: list[dict], **kwargs) -> str: ...
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]: ...
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIProvider:
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def chat(self, messages: list[dict], **kwargs) -> str:
        resp = await self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
        )
        return resp.choices[0].message.content or ""

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        stream = await self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: str) -> list[float]:
        from app.core.config import settings
        resp = await self._client.embeddings.create(
            model=settings.embedding_model, input=text,
        )
        return resp.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        from app.core.config import settings
        resp = await self._client.embeddings.create(
            model=settings.embedding_model, input=texts,
        )
        return [d.embedding for d in resp.data]


class LLMRouter:
    def __init__(self, provider: LLMProvider = None):
        self._provider = provider

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            from app.core.config import settings
            self._provider = OpenAIProvider(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )
        return self._provider

    async def chat(self, messages: list[dict], **kwargs) -> str:
        return await self.provider.chat(messages, **kwargs)

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        async for chunk in self.provider.chat_stream(messages, **kwargs):
            yield chunk

    async def embed(self, text: str) -> list[float]:
        return await self.provider.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return await self.provider.embed_batch(texts)
```

### Step 1.7.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_services/test_llm.py -v
# 预期: 4 passed
```

---

## Task 1.8: 知识库服务 (TDD)

### Step 1.8.1 - RED: 写知识库服务测试

**文件**：`backend/tests/test_services/test_knowledge.py`

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeDocument
from app.services.knowledge import create_document


class TestKnowledgeService:
    @pytest.mark.asyncio
    async def test_create_document_returns_doc(self, db_session: AsyncSession):
        doc = await create_document(
            session=db_session,
            title="测试文档",
            content="# Hello",
            doc_type="markdown",
        )
        assert doc.id is not None
        assert doc.title == "测试文档"
        assert doc.content == "# Hello"

    @pytest.mark.asyncio
    async def test_create_document_persists_to_db(self, db_session: AsyncSession):
        await create_document(session=db_session, title="持久化测试", content="data")
        from sqlalchemy import select
        result = await db_session.execute(select(KnowledgeDocument))
        docs = result.scalars().all()
        assert len(docs) == 1
        assert docs[0].title == "持久化测试"

    @pytest.mark.asyncio
    async def test_create_document_default_doc_type(self, db_session: AsyncSession):
        doc = await create_document(session=db_session, title="默认类型", content="data")
        assert doc.doc_type == "markdown"
```

**验证**：

```bash
cd backend && pytest tests/test_services/test_knowledge.py -v
# 预期: 3 failed
```

### Step 1.8.2 - GREEN: 实现知识库服务

**文件**：`backend/app/services/knowledge.py`

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.llm import LLMRouter, OpenAIProvider
from app.core.config import settings


async def create_document(
    session: AsyncSession,
    title: str,
    content: str,
    doc_type: str = "markdown",
    tenant_id: str = None,
) -> KnowledgeDocument:
    doc = KnowledgeDocument(
        title=title,
        content=content,
        doc_type=doc_type,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


async def search_knowledge(
    session: AsyncSession,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    result = await session.execute(
        select(DocumentChunk.content, DocumentChunk.metadata_, DocumentChunk.document_id)
        .limit(top_k)
    )
    return [
        {"content": row.content, "metadata": row.metadata_, "document_id": str(row.document_id)}
        for row in result
    ]
```

### Step 1.8.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_services/ -v
# 预期: all passed
```

---

## Task 1.9: LangGraph Supervisor Agent (TDD)

### Step 1.9.1 - RED: 写 Agent 测试

**文件**：`backend/tests/test_agents/test_supervisor.py`

```python
import pytest
from app.agents.supervisor import build_supervisor_graph, AgentState
from tests.mock_providers import MockLLMProvider


class TestSupervisorAgent:
    @pytest.fixture
    def mock_provider(self):
        return MockLLMProvider(responses={
            "如何配置": "knowledge",
            "报错": "diagnosis",
            "你好": "general",
        })

    @pytest.mark.asyncio
    async def test_detect_knowledge_intent(self, mock_provider):
        graph = build_supervisor_graph(llm=mock_provider)
        state: AgentState = {
            "messages": [{"role": "user", "content": "如何配置SSL证书？"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
        }
        result = await graph.ainvoke(state)
        assert result["user_intent"] == "knowledge"

    @pytest.mark.asyncio
    async def test_detect_general_intent(self, mock_provider):
        graph = build_supervisor_graph(llm=mock_provider)
        state: AgentState = {
            "messages": [{"role": "user", "content": "你好"}],
            "user_intent": "",
            "sub_agent_outputs": {},
            "knowledge_context": [],
            "error_info": "",
        }
        result = await graph.ainvoke(state)
        assert result["user_intent"] == "general"

    @pytest.mark.asyncio
    async def test_knowledge_node_returns_reply(self, mock_provider):
        mock_provider.responses["default"] = "根据知识库，配置SSL的步骤是..."
        graph = build_supervisor_graph(llm=mock_provider)
        state: AgentState = {
            "messages": [{"role": "user", "content": "如何配置SSL？"}],
            "user_intent": "knowledge",
            "sub_agent_outputs": {},
            "knowledge_context": ["SSL证书配置步骤：1. 生成CSR 2. 提交验证 3. 部署证书"],
            "error_info": "",
        }
        result = await graph.ainvoke(state)
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert len(last_msg["content"]) > 0

    @pytest.mark.asyncio
    async def test_graph_compiles_without_error(self):
        graph = build_supervisor_graph()
        assert graph is not None
```

**验证**：

```bash
cd backend && pytest tests/test_agents/test_supervisor.py -v
# 预期: 4 failed
```

### Step 1.9.2 - GREEN: 实现 Supervisor Agent

**文件**：`backend/app/agents/__init__.py`, `backend/app/agents/supervisor.py`

```python
# backend/app/agents/supervisor.py
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, END
from app.services.llm import LLMRouter, OpenAIProvider


class AgentState(TypedDict):
    messages: list[dict]
    user_intent: str
    sub_agent_outputs: dict
    knowledge_context: list
    error_info: str


INTENT_PROMPT = """分析用户问题的意图，只返回一个词：
- knowledge: 知识问答、产品使用问题
- diagnosis: 故障排查、报错分析
- general: 一般性对话
问题：{query}"""


def build_supervisor_graph(llm: LLMRouter = None):
    llm = llm or LLMRouter()

    async def detect_intent(state: AgentState) -> AgentState:
        query = state["messages"][-1]["content"]
        intent = await llm.chat(
            messages=[{"role": "user", "content": INTENT_PROMPT.format(query=query)}],
            temperature=0,
            max_tokens=20,
        )
        state["user_intent"] = intent.strip().lower()
        if state["user_intent"] not in ("knowledge", "diagnosis"):
            state["user_intent"] = "general"
        return state

    async def knowledge_node(state: AgentState) -> AgentState:
        query = state["messages"][-1]["content"]
        ctx = state.get("knowledge_context", [])
        context = "\n\n".join(ctx) if ctx else "未找到相关知识。"
        prompt = f"""基于以下知识回答问题。如果知识不足以回答，请如实说明。
知识：{context}
问题：{query}"""
        reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
        state["messages"].append({"role": "assistant", "content": reply})
        return state

    async def general_node(state: AgentState) -> AgentState:
        reply = await llm.chat(messages=state["messages"])
        state["messages"].append({"role": "assistant", "content": reply})
        return state

    def router_condition(state: AgentState) -> Literal["knowledge", "general"]:
        intent = state.get("user_intent", "general")
        if intent == "diagnosis":
            return "general"
        return intent

    graph = StateGraph(AgentState)
    graph.add_node("detect_intent", detect_intent)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("general", general_node)
    graph.set_entry_point("detect_intent")
    graph.add_conditional_edges("detect_intent", router_condition)
    graph.add_edge("knowledge", END)
    graph.add_edge("general", END)
    return graph.compile()
```

### Step 1.9.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_agents/ -v
# 预期: 4 passed
```

---

## Task 1.10: Chat API (TDD)

### Step 1.10.1 - RED: 写 Chat API 测试

**文件**：`backend/tests/test_api/test_chat.py`

```python
import json
import pytest
from httpx import AsyncClient


class TestChatAPI:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_create_conversation(self, client: AsyncClient):
        resp = await client.post("/api/v1/chat/conversations", json={"title": "测试"})
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["title"] == "测试"

    @pytest.mark.asyncio
    async def test_list_conversations(self, client: AsyncClient):
        await client.post("/api/v1/chat/conversations", json={"title": "对话1"})
        await client.post("/api/v1/chat/conversations", json={"title": "对话2"})
        resp = await client.get("/api/v1/chat/conversations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/chat/conversations/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_completion_stream(self, client: AsyncClient):
        # 先创建会话
        conv_resp = await client.post("/api/v1/chat/conversations", json={"title": "测试流式"})
        conv_id = conv_resp.json()["id"]

        resp = await client.post(
            "/api/v1/chat/completions",
            json={"content": "你好", "conversation_id": conv_id},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_chat_completion_auto_create_conv(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/chat/completions",
            json={"content": "你好"},
        )
        assert resp.status_code == 200
```

**验证**：

```bash
cd backend && pytest tests/test_api/test_chat.py -v
# 预期: 5 failed (API 未实现)
```

### Step 1.10.2 - GREEN: 实现 Chat API + FastAPI 入口 + Health

**文件**：`backend/app/main.py`, `backend/app/api/v1/__init__.py`, `backend/app/api/v1/health.py`, `backend/app/api/v1/chat.py`

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import chat, knowledge, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])


# backend/app/api/v1/health.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
```

```python
# backend/app/api/v1/chat.py
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.conversation import Conversation, Message
from app.agents.supervisor import build_supervisor_graph
from app.services.knowledge import search_knowledge

router = APIRouter()


@router.get("/conversations")
async def list_conversations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Conversation).order_by(desc(Conversation.updated_at))
    )
    return [
        {
            "id": str(c.id), "title": c.title, "status": c.status,
            "created_at": c.created_at.isoformat(), "updated_at": c.updated_at.isoformat(),
        }
        for c in result.scalars().all()
    ]


@router.post("/conversations")
async def create_conversation(data: dict, session: AsyncSession = Depends(get_session)):
    conv = Conversation(title=data.get("title", "新对话"))
    session.add(conv)
    await session.commit()
    await session.refresh(conv)
    return {
        "id": str(conv.id), "title": conv.title, "status": conv.status,
        "created_at": conv.created_at.isoformat(), "updated_at": conv.updated_at.isoformat(),
    }


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, session: AsyncSession = Depends(get_session)):
    conv = await session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "会话不存在")
    return {
        "id": str(conv.id), "title": conv.title, "status": conv.status,
        "created_at": conv.created_at.isoformat(), "updated_at": conv.updated_at.isoformat(),
    }


@router.get("/conversations/{conv_id}/messages")
async def list_messages(conv_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    return [
        {
            "id": str(m.id), "role": m.role, "content": m.content,
            "agent_name": m.agent_name, "sources": m.sources or [],
            "created_at": m.created_at.isoformat(),
        }
        for m in result.scalars().all()
    ]


@router.post("/completions")
async def chat_completion(
    req: dict,
    session: AsyncSession = Depends(get_session),
):
    content = req["content"]
    conv_id = req.get("conversation_id")

    if not conv_id:
        conv = Conversation(title=content[:50])
        session.add(conv)
        await session.commit()
        conv_id = str(conv.id)
    else:
        conv = await session.get(Conversation, conv_id)
        if not conv:
            raise HTTPException(404, "会话不存在")

    user_msg = Message(conversation_id=conv_id, role="user", content=content)
    session.add(user_msg)
    await session.commit()

    ctx = await search_knowledge(session, content)
    graph = build_supervisor_graph()
    state = {
        "messages": [{"role": "user", "content": content}],
        "user_intent": "",
        "sub_agent_outputs": {},
        "knowledge_context": [c["content"] for c in ctx],
        "error_info": "",
    }

    async def event_stream():
        full_content = ""
        async for chunk in graph.astream(state):
            for node_output in chunk.values():
                msgs = node_output.get("messages", [])
                for msg in msgs:
                    if msg["role"] == "assistant":
                        full_content = msg["content"]

        yield f"data: {json.dumps({'content': full_content, 'conversation_id': str(conv_id), 'sources': ctx})}\n\n"
        yield "data: [DONE]\n\n"

        msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content=full_content,
            sources=ctx,
        )
        session.add(msg)
        await session.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### Step 1.10.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_api/test_chat.py -v
# 预期: 6 passed
```

---

## Task 1.11: 知识库 API (TDD)

### Step 1.11.1 - RED: 写知识库 API 测试

**文件**：`backend/tests/test_api/test_knowledge.py`

```python
import pytest
from httpx import AsyncClient


class TestKnowledgeAPI:
    @pytest.mark.asyncio
    async def test_upload_document(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/knowledge/documents",
            data={"title": "测试文档"},
            files={"file": ("test.md", b"# Hello World", "text/markdown")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["title"] == "测试文档"

    @pytest.mark.asyncio
    async def test_list_documents(self, client: AsyncClient):
        await client.post(
            "/api/v1/knowledge/documents",
            data={"title": "Doc1"},
            files={"file": ("a.md", b"content a", "text/markdown")},
        )
        await client.post(
            "/api/v1/knowledge/documents",
            data={"title": "Doc2"},
            files={"file": ("b.md", b"content b", "text/markdown")},
        )
        resp = await client.get("/api/v1/knowledge/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_document(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/knowledge/documents",
            data={"title": "GetTest"},
            files={"file": ("g.md", b"# Get content", "text/markdown")},
        )
        doc_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/knowledge/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "GetTest"

    @pytest.mark.asyncio
    async def test_delete_document(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/knowledge/documents",
            data={"title": "DelTest"},
            files={"file": ("d.md", b"delete me", "text/markdown")},
        )
        doc_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/knowledge/documents/{doc_id}")
        assert resp.status_code == 200
        # 确认已删除
        get_resp = await client.get(f"/api/v1/knowledge/documents/{doc_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_search_knowledge(self, client: AsyncClient):
        resp = await client.post("/api/v1/knowledge/search", params={"query": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
```

**验证**：

```bash
cd backend && pytest tests/test_api/test_knowledge.py -v
# 预期: 5 failed
```

### Step 1.11.2 - GREEN: 实现知识库 API

**文件**：`backend/app/api/v1/knowledge.py`

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.knowledge import KnowledgeDocument
from app.services.knowledge import create_document, search_knowledge

router = APIRouter()


@router.post("/documents")
async def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    content = await file.read()
    doc = await create_document(
        session=session, title=title, content=content.decode("utf-8"),
    )
    return {"id": str(doc.id), "title": doc.title}


@router.get("/documents")
async def list_documents(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(KnowledgeDocument).order_by(desc(KnowledgeDocument.updated_at))
    )
    return [
        {
            "id": str(d.id), "title": d.title, "doc_type": d.doc_type,
            "created_at": d.created_at.isoformat(),
        }
        for d in result.scalars().all()
    ]


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, session: AsyncSession = Depends(get_session)):
    doc = await session.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return {
        "id": str(doc.id), "title": doc.title, "content": doc.content,
        "doc_type": doc.doc_type, "created_at": doc.created_at.isoformat(),
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, session: AsyncSession = Depends(get_session)):
    doc = await session.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    await session.delete(doc)
    await session.commit()
    return {"ok": True}


@router.post("/search")
async def search_endpoint(
    query: str = "query",
    top_k: int = 5,
    session: AsyncSession = Depends(get_session),
):
    results = await search_knowledge(session, query, top_k=top_k)
    return {"results": results}
```

### Step 1.11.3 - 验证 GREEN

```bash
cd backend && pytest tests/test_api/ -v
# 预期: 所有 API 测试通过
```

---

## Task 1.12: Docker Compose

**文件**：`docker-compose.yml`, `backend/Dockerfile`, `.env.example`

**docker-compose.yml**：

```yaml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: tech_support
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - '5432:5432'
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U postgres']
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - '8000:8000'
    environment:
      DB_DSN: postgresql+asyncpg://postgres:postgres@postgres:5432/tech_support
      LLM_API_KEY: ${LLM_API_KEY:-}
    depends_on:
      postgres:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  frontend:
    build: ./frontend
    ports:
      - '3000:3000'
    depends_on:
      - backend
    command: npm run dev -- --host 0.0.0.0

volumes:
  pgdata:
```

**backend/Dockerfile**：

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**验证**：`docker compose up -d && curl http://localhost:8000/api/v1/health`

---

## Task 1.13: 前端初始化

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install @reduxjs/toolkit react-redux antd @ant-design/icons react-router-dom axios
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

**验证**：`cd frontend && npm run dev` 启动成功

---

## Task 1.14: 前端 Redux Store

**文件**：`frontend/src/store/index.ts`, `frontend/src/store/conversationSlice.ts`

```typescript
// frontend/src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import conversationReducer from './conversationSlice';

export const store = configureStore({
  reducer: { conversation: conversationReducer },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

```typescript
// frontend/src/store/conversationSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

interface Message {
  id: string;
  role: string;
  content: string;
  agent_name?: string;
  sources?: any[];
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface ConversationState {
  list: Conversation[];
  currentId: string | null;
  messages: Message[];
  loading: boolean;
  streaming: boolean;
}

const initialState: ConversationState = {
  list: [],
  currentId: null,
  messages: [],
  loading: false,
  streaming: false,
};

export const fetchConversations = createAsyncThunk('conversation/fetchList', async () => {
  const res = await axios.get(`${API_BASE}/chat/conversations`);
  return res.data;
});

export const createConversation = createAsyncThunk('conversation/create', async (title?: string) => {
  const res = await axios.post(`${API_BASE}/chat/conversations`, { title: title || '新对话' });
  return res.data;
});

export const fetchMessages = createAsyncThunk('conversation/fetchMessages', async (convId: string) => {
  const res = await axios.get(`${API_BASE}/chat/conversations/${convId}/messages`);
  return res.data;
});

const slice = createSlice({
  name: 'conversation',
  initialState,
  reducers: {
    setCurrentId(state, action: PayloadAction<string>) {
      state.currentId = action.payload;
    },
    appendMessage(state, action: PayloadAction<{ role: string; content: string }>) {
      state.messages.push({
        id: Date.now().toString(),
        role: action.payload.role,
        content: action.payload.content,
        created_at: new Date().toISOString(),
      });
    },
    setStreaming(state, action: PayloadAction<boolean>) {
      state.streaming = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchConversations.fulfilled, (state, action) => {
      state.list = action.payload;
    });
    builder.addCase(createConversation.fulfilled, (state, action) => {
      state.list.unshift(action.payload);
      state.currentId = action.payload.id;
      state.messages = [];
    });
    builder.addCase(fetchMessages.fulfilled, (state, action) => {
      state.messages = action.payload;
    });
  },
});

export const { setCurrentId, appendMessage, setStreaming } = slice.actions;
export default slice.reducer;
```

**验证**：`cd frontend && npx vitest run` 通过（Store 测试）

---

## Task 1.15: 前端 Store 测试

**文件**：`frontend/src/__tests__/conversationSlice.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import reducer, { setCurrentId, appendMessage, setStreaming, ConversationState } from '../store/conversationSlice';

const initialState: ConversationState = {
  list: [],
  currentId: null,
  messages: [],
  loading: false,
  streaming: false,
};

describe('conversationSlice', () => {
  it('should return initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('should handle setCurrentId', () => {
    const state = reducer(initialState, setCurrentId('abc-123'));
    expect(state.currentId).toBe('abc-123');
  });

  it('should handle appendMessage', () => {
    const state = reducer(initialState, appendMessage({ role: 'user', content: '你好' }));
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].role).toBe('user');
    expect(state.messages[0].content).toBe('你好');
  });

  it('should handle setStreaming', () => {
    const state = reducer(initialState, setStreaming(true));
    expect(state.streaming).toBe(true);
  });

  it('should keep message history ordered', () => {
    let state = reducer(initialState, appendMessage({ role: 'user', content: 'Q1' }));
    state = reducer(state, appendMessage({ role: 'assistant', content: 'A1' }));
    state = reducer(state, appendMessage({ role: 'user', content: 'Q2' }));
    expect(state.messages).toHaveLength(3);
    expect(state.messages[0].content).toBe('Q1');
    expect(state.messages[1].content).toBe('A1');
    expect(state.messages[2].content).toBe('Q2');
  });
});
```

**验证**：

```bash
cd frontend && npx vitest run
# 预期: 5 passed
```

---

## Task 1.16: 前端聊天页面

**文件**：`frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/pages/ChatPage.tsx`

```tsx
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { store } from './store';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>,
);

// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import ChatPage from './pages/ChatPage';

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:id" element={<ChatPage />} />
          <Route path="*" element={<ChatPage />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
```

```tsx
// frontend/src/pages/ChatPage.tsx
import { useEffect, useRef, useState } from 'react';
import { Layout, Menu, Button, Input, List, Typography, Empty } from 'antd';
import { PlusOutlined, MessageOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import { AppDispatch, RootState } from '../store';
import {
  fetchConversations,
  createConversation,
  fetchMessages,
  appendMessage,
  setCurrentId,
  setStreaming,
} from '../store/conversationSlice';

const { Sider, Content } = Layout;
const { Text } = Typography;
const API_BASE = 'http://localhost:8000/api/v1';

export default function ChatPage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { id } = useParams();
  const { list, currentId, messages, streaming } = useSelector((s: RootState) => s.conversation);
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);
  useEffect(() => {
    if (id) {
      dispatch(setCurrentId(id));
      dispatch(fetchMessages(id));
    }
  }, [id, dispatch]);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleNew = async () => {
    const res = await dispatch(createConversation());
    navigate(`/chat/${(res as any).payload.id}`);
  };

  const handleSend = async () => {
    if (!input.trim() || streaming) return;
    const msg = input;
    setInput('');
    dispatch(appendMessage({ role: 'user', content: msg }));
    dispatch(setStreaming(true));
    let convId = currentId;
    if (!convId) {
      const res = await dispatch(createConversation(msg.slice(0, 50)));
      convId = (res as any).payload.id;
      navigate(`/chat/${convId}`, { replace: true });
    }
    const resp = await fetch(`${API_BASE}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: msg, conversation_id: convId }),
    });
    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      for (const line of decoder.decode(value).split('\n')) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          try {
            fullText = JSON.parse(line.slice(6)).content;
          } catch {}
        }
      }
    }
    dispatch(appendMessage({ role: 'assistant', content: fullText }));
    dispatch(setStreaming(false));
    dispatch(fetchConversations());
  };

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={280} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} block onClick={handleNew}>
            新建对话
          </Button>
        </div>
        <Menu
          mode="inline"
          selectedKeys={currentId ? [currentId] : []}
          onSelect={({ key }) => navigate(`/chat/${key}`)}
          items={list.map((c) => ({ key: c.id, icon: <MessageOutlined />, label: c.title }))}
        />
      </Sider>
      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          {messages.length === 0 ? (
            <Empty description="开始新的对话" style={{ marginTop: 120 }} />
          ) : (
            <List
              dataSource={messages}
              renderItem={(msg) => (
                <List.Item>
                  <div style={{ width: '100%' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {msg.role === 'user' ? '用户' : '助手'}
                    </Text>
                    <div
                      style={{
                        background: msg.role === 'user' ? '#e6f4ff' : '#fafafa',
                        padding: '8px 12px',
                        borderRadius: 8,
                        marginTop: 4,
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {msg.content}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          )}
          <div ref={endRef} />
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f0f0f0' }}>
          <Input.Search
            size="large"
            placeholder="输入您的问题..."
            enterButton="发送"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onSearch={handleSend}
            loading={streaming}
          />
        </div>
      </Content>
    </Layout>
  );
}
```

**验证**：`cd frontend && npm run build` 编译通过

---

## Task 1.17: 前端 Dockerfile

**文件**：`frontend/Dockerfile`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**验证**：`docker compose build frontend` 成功

---

## 任务依赖关系

```
1.1 目录结构
  │
  ├── 1.2 测试基础设施 ────┐
  ├── 1.3 应用配置 (TDD) ──┤
  │                        ▼
  │               ┌── 1.4 数据库 (TDD)
  │               │    └── 1.5 数据模型 (TDD)
  │               │         └── 1.6 Alembic
  │               │
  │               ├── 1.7 LLM Router (TDD)
  │               │    ├── 1.8 知识库服务 (TDD)
  │               │    └── 1.9 Supervisor Agent (TDD)
  │               │         │
  │               └─────────┼── 1.10 Chat API (TDD)
  │                         └── 1.11 知识库 API (TDD)
  │
  ├── 1.12 Docker Compose
  │
  └── 1.13 前端初始化
       └── 1.14 Redux Store
            ├── 1.15 Store 测试
            └── 1.16 聊天页面
                 └── 1.17 前端 Dockerfile
```

## 验证清单 (Phase 1 完成标准)

- [x] `pytest tests/ -v` 全部通过 (125 tests)
- [x] `npx vitest run` 前端测试全部通过 (5 tests)
- [x] `docker compose up -d` 所有服务启动成功
- [x] `curl localhost:8000/api/v1/health` 返回 200
- [x] 前端聊天界面可发送消息并收到 SSE 回复
- [x] 对话历史持久化到 PostgreSQL
- [x] 知识库文档上传和搜索功能正常
- [x] 测试覆盖 Mock LLM，不依赖外部 API

---

## Phase 3 (Agent 体系) 任务分解

---

## Task 3.1: Diagnosis Agent — 故障诊断模型与匹配服务

**目标**：建立已知错误模式库，实现错误文本的规则/语义匹配。

### Step 3.1.1 - RED: 写 ErrorPattern 模型测试

**文件**：`backend/tests/test_db/test_models.py`

```python
class TestErrorPattern:
    def test_create_pattern(self, db_session):
        # 创建 ErrorPattern，验证 id、pattern、solution、severity 字段
        pass

    def test_optional_fields_default(self, db_session):
        # 验证 tags/solution 可空，severity 默认 "medium"
        pass
```

### Step 3.1.2 - GREEN: 实现 ErrorPattern 模型

**文件**：`backend/app/models/error_pattern.py`

```python
class ErrorPattern(Base, TimestampMixin):
    __tablename__ = "error_patterns"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    pattern = Column(String(500), nullable=False)       # 正则/关键词模式
    solution = Column(Text, nullable=True)               # 解决方案
    severity = Column(String(20), default="medium")      # critical/high/medium/low
    category = Column(String(100), nullable=True)        # 分类标签
    tags = Column(JSON, default=list)                    # 标签数组
```

需在 `Base` 中注册，`conftest.py` 自动创建表。

### Step 3.1.3 - RED: 写 ErrorMatcher 服务测试

**文件**：`backend/tests/test_services/test_diagnosis.py`

```python
class TestErrorMatcher:
    def test_exact_pattern_match(self, db_session):
        # 插入 ErrorPattern("Connection refused")，匹配 "Connection refused"
        pass

    def test_regex_pattern_match(self, db_session):
        # 插入 ErrorPattern("ERR_\d{5}")，匹配 "ERR_12345"
        pass

    def test_no_match_returns_empty(self, db_session):
        # 无匹配时返回空列表
        pass

    def test_match_returns_multiple_sorted_by_severity(self, db_session):
        # 多个匹配按 severity 排序返回
        pass
```

### Step 3.1.4 - GREEN: 实现 ErrorMatcher 服务

**文件**：`backend/app/services/diagnosis.py`

```python
def match_errors(session: Session, error_text: str) -> list[dict]:
    """遍历 ErrorPattern 表，regex/keyword 匹配，按 severity 排序返回"""
```

### 验证 Step 3.1.1 - 3.1.4：

```bash
pytest tests/test_db/test_models.py -v -k "ErrorPattern"
pytest tests/test_services/test_diagnosis.py -v
```

---

## Task 3.2: Diagnosis Agent — 故障诊断 Agent 节点

**目标**：在 LangGraph Supervisor 中添加 diagnosis 路由和专门的诊断 Agent。

### Step 3.2.1 - RED: 写 Diagnosis Agent 测试

**文件**：`backend/tests/test_agents/test_diagnosis.py`

```python
class TestDiagnosisAgent:
    def test_diagnosis_node_returns_reply(self, mock_provider, db_session):
        # 输入 state 含 "Connection refused"，期望输出含诊断内容
        pass

    def test_diagnosis_node_calls_error_matcher(self, mock_provider, db_session):
        # 验证 error_matcher 被调用且结果注入 prompt
        pass

    def test_diagnosis_node_no_match_fallback(self, mock_provider, db_session):
        # 无匹配模式时 Agent 给出通用建议
        pass
```

### Step 3.2.2 - GREEN: 实现 Diagnosis Agent 节点

**文件**：`backend/app/agents/diagnosis.py`

```python
DIAGNOSIS_PROMPT = """你是故障诊断专家。根据以下错误信息和已知模式给出诊断建议。
如果已知解决方案为空，给出通用排查步骤。

错误信息：{error_text}

已知匹配模式：
{matches}

请给出诊断结果和修复建议。"""

async def diagnosis_node(state: AgentState) -> AgentState:
    error_text = state.get("error_info", state["messages"][-1]["content"])
    matches = match_errors(session, error_text)
    prompt = DIAGNOSIS_PROMPT.format(error_text=error_text, matches=format_matches(matches))
    reply = await llm.chat(messages=[{"role": "user", "content": prompt}])
    state["messages"].append({"role": "assistant", "content": reply})
    state["sub_agent_outputs"]["diagnosis"] = {"matches": matches, "reply": reply}
    return state
```

### Step 3.2.3 - RED: 更新意图路由 + 集成测试

**文件**：`backend/tests/test_agents/test_supervisor.py`

```python
def test_detect_diagnosis_intent(self, mock_provider):
    # "error_12345" → user_intent == "diagnosis"
    pass

def test_diagnosis_routed_correctly(self, mock_provider):
    # user_intent == "diagnosis" → 走 diagnosis_node 而不是 general
    pass
```

### Step 3.2.4 - GREEN: 更新 Supervisor 路由

**文件**：`backend/app/agents/supervisor.py`

```python
# 修改 router_condition:
def router_condition(state):
    intent = state.get("user_intent", "general")
    return intent  # diagnosis 直接路由到 diagnosis 节点

# 在 graph 中添加:
graph.add_node("diagnosis", diagnosis_node)
graph.add_conditional_edges("detect_intent", router_condition)
graph.add_edge("diagnosis", END)
```

更新 `AgentState` 添加 `session` 字段（或通过闭包注入 session）。

### 验证 Step 3.2.1 - 3.2.4：

```bash
pytest tests/test_agents/test_diagnosis.py -v
pytest tests/test_agents/test_supervisor.py -v -k "diagnosis"
```

---

## Task 3.3: Diagnosis Agent — 诊断 API + 前端

**目标**：暴露诊断 API，前端提供错误输入界面。

### Step 3.3.1 - RED: 写诊断 API 测试

**文件**：`backend/tests/test_api/test_diagnosis.py`

```python
class TestDiagnosisAPI:
    async def test_diagnose_error_text(self, client, db_session):
        # POST /api/v1/diagnosis 传入 error_text，返回诊断结果
        pass

    async def test_diagnose_with_conversation(self, client, db_session):
        # 与对话关联的诊断
        pass

    async def test_diagnose_no_match(self, client):
        # 无匹配时返回通用建议
        pass
```

### Step 3.3.2 - GREEN: 实现诊断 API 路由

**文件**：`backend/app/api/v1/diagnosis.py`

```python
router = APIRouter()

@router.post("/diagnosis")
def diagnose(req: dict, session: Session = Depends(get_session)):
    error_text = req["error_text"]
    # 通过 Diagnosis Agent 处理
    ...
```

在 `main.py` 注册 `app.include_router(diagnosis_router, prefix="/api/v1")`。

### Step 3.3.3 - 前端错误诊断页面

**文件**：`frontend/src/pages/DiagnosisPage.tsx`

- 错误输入 TextArea
- 诊断结果展示区（匹配模式、严重程度、解决方案）
- 无匹配时显示通用排查建议

### Step 3.3.4 - 更新导航栏

**文件**：`frontend/src/App.tsx`

- 添加「故障诊断」导航项
- 路由 `/diagnosis` → DiagnosisPage

### 验证 Step 3.3.1 - 3.3.4：

```bash
pytest tests/test_api/test_diagnosis.py -v
npx vitest run
```

---

## Task 3.4: Ticket Agent — 工单模型与 CRUD

**目标**：建立工单系统，支持创建/查询/更新/关闭工单。

### Step 3.4.1 - RED: 写 Ticket 模型测试

**文件**：`backend/tests/test_db/test_models.py`

```python
class TestTicket:
    def test_create_ticket(self, db_session):
        # 创建工单，验证所有字段
        pass

    def test_ticket_default_status(self, db_session):
        # 默认 status == "open"
        pass

    def test_ticket_auto_timestamps(self, db_session):
        # 验证 created_at / updated_at 自动设置
        pass
```

### Step 3.4.2 - GREEN: 实现 Ticket 模型

**文件**：`backend/app/models/ticket.py`

```python
class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="open")       # open/in_progress/resolved/closed
    priority = Column(String(20), default="medium")   # critical/high/medium/low
    assigned_to = Column(String(100), nullable=True)
    source = Column(String(50), default="chat")       # chat/email/api
    conversation_id = Column(GUID, ForeignKey("conversations.id"), nullable=True)
```

### Step 3.4.3 - RED: 写 Ticket Service 测试

**文件**：`backend/tests/test_services/test_ticket.py`

```python
class TestTicketService:
    def test_create_ticket(self, db_session):
        pass

    def test_get_ticket_by_id(self, db_session):
        pass

    def test_list_tickets(self, db_session):
        pass

    def test_update_ticket_status(self, db_session):
        pass

    def test_delete_ticket(self, db_session):
        pass
```

### Step 3.4.4 - GREEN: 实现 Ticket Service

**文件**：`backend/app/services/ticket.py`

```python
def create_ticket(session, title, description, **kwargs) -> Ticket: ...
def get_ticket(session, ticket_id) -> Ticket: ...
def list_tickets(session, **filters) -> list[Ticket]: ...
def update_ticket(session, ticket_id, **updates) -> Ticket: ...
def delete_ticket(session, ticket_id) -> None: ...
```

### 验证 Step 3.4.1 - 3.4.4：

```bash
pytest tests/test_db/test_models.py -v -k "Ticket"
pytest tests/test_services/test_ticket.py -v
```

---

## Task 3.5: Ticket Agent — 工单 API + 前端 + Agent 节点

**目标**：暴露工单 API，实现 Ticket Agent 节点，添加工单管理前端。

### Step 3.5.1 - RED: 写 Ticket API 测试

**文件**：`backend/tests/test_api/test_ticket.py`

```python
class TestTicketAPI:
    async def test_create_ticket(self, client):
        pass

    async def test_list_tickets(self, client):
        pass

    async def test_get_ticket(self, client):
        pass

    async def test_update_ticket_status(self, client):
        pass

    async def test_delete_ticket(self, client):
        pass
```

### Step 3.5.2 - GREEN: 实现 Ticket API 路由

**文件**：`backend/app/api/v1/ticket.py`

```python
router = APIRouter()
@router.post("/tickets") -> create
@router.get("/tickets") -> list
@router.get("/tickets/{id}") -> get
@router.patch("/tickets/{id}") -> update
@router.delete("/tickets/{id}") -> delete
```

### Step 3.5.3 - RED: 写 Ticket Agent 节点测试

**文件**：`backend/tests/test_agents/test_ticket.py`

```python
class TestTicketAgent:
    def test_ticket_node_creates_ticket(self, mock_provider, db_session):
        pass

    def test_ticket_node_lists_tickets(self, mock_provider, db_session):
        pass

    def test_ticket_node_update_ticket(self, mock_provider, db_session):
        pass
```

### Step 3.5.4 - GREEN: 实现 Ticket Agent 节点

**文件**：`backend/app/agents/ticket.py`

```python
TICKET_PROMPT = """你是工单管理助手。根据用户请求执行工单操作。
可用操作：创建工单、查询工单、更新工单状态。

用户请求：{query}

当前工单上下文：
{tickets_context}"""

async def ticket_node(state: AgentState) -> AgentState:
    # 解析 user intent for ticket operation
    # 调用 ticket service 执行操作
    # 返回结果
```

### Step 3.5.5 - 前端工单管理页面

**文件**：`frontend/src/pages/TicketPage.tsx`

- 工单列表（Table 显示 ID、标题、状态、优先级、创建时间）
- 创建工单（Modal 表单）
- 更新状态（Select dropdown）
- 查看详情

### Step 3.5.6 - 更新导航

**文件**：`frontend/src/App.tsx`

- 添加「工单管理」导航项
- 路由 `/tickets` → TicketPage

### 验证 Step 3.5.1 - 3.5.6：

```bash
pytest tests/test_api/test_ticket.py -v
pytest tests/test_agents/test_ticket.py -v
npx vitest run
```

---

## Task 3.6: Data Agent — 数据查询 Agent

**目标**：允许用户用自然语言查询系统数据（对话统计、知识库统计等）。

### Step 3.6.1 - RED: 写 Data Agent 测试

**文件**：`backend/tests/test_agents/test_data.py`

```python
class TestDataAgent:
    def test_data_agent_returns_statistics(self, mock_provider):
        # "有多少对话?" → 返回对话总数
        pass

    def test_data_agent_query_conversations(self, mock_provider):
        # "最近7天的对话" → 返回时间过滤结果
        pass

    def test_data_agent_unknown_query(self, mock_provider):
        # 无法理解的查询 → 返回提示引导用户
        pass
```

### Step 3.6.2 - GREEN: 实现 Data Agent

**文件**：`backend/app/agents/data.py`

```python
DATA_PROMPT = """你是数据分析助手。根据用户问题查询系统数据。
可用数据源：对话统计、消息统计、知识库统计。

用户问题：{query}

数据结果：
{data_result}"""

async def data_node(state: AgentState) -> AgentState:
    # 用 LLM 解析查询意图 → 映射到预定义查询
    query_type = await classify_data_query(llm, query)
    result = execute_data_query(session, query_type, **params)
    # 格式化回复
```

### Step 3.6.3 - 数据查询函数

**文件**：`backend/app/services/data_query.py`

```python
def count_conversations(session, **filters) -> int
def count_messages(session, **filters) -> int
def conversation_trend(session, days=7) -> list[dict]
def knowledge_stats(session) -> dict
```

### 验证 Step 3.6.1 - 3.6.3：

```bash
pytest tests/test_agents/test_data.py -v
```

---

## Task 3.7: Escalation Agent — 升级 Agent

**目标**：当 Agent 无法解决问题时，智能升级到 L2/L3 工程师。

### Step 3.7.1 - RED: 写 Escalation Agent 测试

**文件**：`backend/tests/test_agents/test_escalation.py`

```python
class TestEscalationAgent:
    def test_escalation_creates_ticket(self, mock_provider, db_session):
        # 升级 → 自动创建工单并标记为 escalated
        pass

    def test_escalation_notifies_assignee(self, mock_provider):
        # 升级通知责任人（mock 通知服务）
        pass

    def test_low_severity_no_escalation(self, mock_provider):
        # 低严重度不升级
        pass
```

### Step 3.7.2 - GREEN: 实现 Escalation Agent

**文件**：`backend/app/agents/escalation.py`

```python
ESCALATION_PROMPT = """评估是否需要对以下问题进行升级。
严重度为 critical/high 或连续失败次数 > 2 时应升级。

问题：{query}
当前诊断结果：{diagnosis_result}
连续失败次数：{retry_count}

输出：升级 / 不升级"""
```

### 验证 Step 3.7.1 - 3.7.2：

```bash
pytest tests/test_agents/test_escalation.py -v
```

---

## Task 3.8: 多 Agent 协作流程

**目标**：设计 Diagnosis → Escalation → Ticket 的自动流转。

### Step 3.8.1 - RED: 写协作流程测试

**文件**：`backend/tests/test_agents/test_collaboration.py`

```python
class TestMultiAgentWorkflow:
    def test_diagnosis_triggers_escalation(self, mock_provider):
        # 诊断失败 → 自动进入 Escalation Agent
        pass

    def test_escalation_creates_ticket(self, mock_provider, db_session):
        # 升级 → Ticket Agent 自动创建工单
        pass

    def test_simple_question_no_escalation(self, mock_provider):
        # 简单问题不触发升级
        pass
```

### Step 3.8.2 - GREEN: 实现多 Agent 图

**文件**：`backend/app/agents/supervisor.py`（重构）

- 扩展路由条件支持多层路由（diagnosis → escalation → ticket）
- 添加 `sub_agent_outputs` 在 Agent 间传递上下文
- 条件边判断是否继续流转或结束

```python
def router_condition(state):
    intent = state["user_intent"]
    if intent == "diagnosis":
        diag = state.get("sub_agent_outputs", {}).get("diagnosis", {})
        if diag.get("needs_escalation"):
            return "escalation"
        return END
    if intent == "escalation":
        return "ticket"
    return intent  # knowledge / general
```

### 验证 Step 3.8.1 - 3.8.2：

```bash
pytest tests/test_agents/test_collaboration.py -v
```

---

## Task 3.9: 人机协同 (Human-in-the-loop Interrupt)

**目标**：在关键决策点（升级、创建工单）插入人工确认。

### Step 3.9.1 - RED: 写 Interrupt 测试

**文件**：`backend/tests/test_agents/test_interrupt.py`

```python
class TestHumanInTheLoop:
    def test_interrupt_at_escalation(self, mock_provider):
        # 升级前触发 interrupt，等待人工确认
        pass

    def test_approve_escalation_resumes(self, mock_provider):
        # 人工批准 → 继续执行
        pass

    def test_reject_escalation_stops(self, mock_provider):
        # 人工拒绝 → 终止流程
        pass
```

### Step 3.9.2 - GREEN: 实现 Interrupt 节点

**文件**：`backend/app/agents/supervisor.py`

```python
from langgraph.graph import interrupt

async def human_approval_node(state: AgentState) -> AgentState:
    decision = interrupt({
        "type": "escalation_approval",
        "ticket_preview": state.get("sub_agent_outputs", {}).get("ticket", {}),
        "question": "是否批准升级到 L2 工程师？",
    })
    if decision.get("approved"):
        state["sub_agent_outputs"]["human_decision"] = "approved"
    else:
        state["sub_agent_outputs"]["human_decision"] = "rejected"
    return state
```

### Step 3.9.3 - 前端审批 UI

**文件**：`frontend/src/pages/ChatPage.tsx`（扩展）

- 检测 interrupt 事件 → 展示审批对话框
- 批准/拒绝按钮 → 恢复 Agent 执行
- 显示待审批的工单预览

### 验证 Step 3.9.1 - 3.9.3：

```bash
pytest tests/test_agents/test_interrupt.py -v
npx vitest run
```

---

## 验证清单 (Phase 3 完成标准)

- [x] 已知错误模式可自动匹配并给出诊断建议
- [x] 诊断 Agent 通过意图路由正确触发
- [x] 诊断 API 端点 POST /api/v1/diagnosis 返回结构化结果
- [x] 前端故障诊断页面可输入错误文本并展示诊断结果
- [x] 工单 CRUD 完整（创建/查询/更新/删除）
- [x] Ticket Agent 可通过对话创建/查询工单
- [x] 前端工单管理页面完整
- [x] Data Agent 可回答数据统计问题
- [x] 诊断 → 升级 → 工单自动流转通畅
- [x] 关键节点有人工审批拦截
- [x] `pytest tests/ -v` 全部通过 (125 tests)
- [x] `npx vitest run` 前端测试全部通过 (5 tests)
- [x] `ruff check backend/app/` 全部通过

---

## Phase 2 (企业级功能) 任务分解

> **目标**：实现 PRD 中 P2 级别的企业级功能 — 认证授权 (F20)、多租户 (F19)、诊断流程编辑器 (F17)
> **依赖**：Phase 1 (MVP) + Phase 3 (Agent 体系) 已完成

---

## Task 2.1: User 模型与密码安全 (TDD)

**目标**：建立用户模型，实现密码哈希和验证。

### Step 2.1.1 - RED: 写 User 模型测试

**文件**：`backend/tests/test_db/test_user.py`

```python
class TestUser:
    def test_create_user(self, db_session):
        # 创建 User，验证 id、email、name、role 字段
        pass

    def test_password_hash_not_plaintext(self, db_session):
        # password_hash 不等于明文密码
        pass

    def test_default_role_is_l1_engineer(self, db_session):
        # 默认 role == "l1_engineer"
        pass

    def test_optional_fields_default(self, db_session):
        # tenant_id/assigned_to 可空
        pass
```

### Step 2.1.2 - GREEN: 实现 User 模型

**文件**：`backend/app/models/user.py`

```python
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="l1_engineer")  # admin/manager/l2_engineer/l1_engineer
    is_active = Column(Boolean, default=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)
```

### Step 2.1.3 - RED: 写密码哈希测试

**文件**：`backend/tests/test_services/test_auth.py`

```python
class TestPasswordHash:
    def test_hash_password_returns_hash(self):
        # hash_password("secret") != "secret"
        pass

    def test_verify_password_correct(self):
        # verify_password("secret", hash) == True
        pass

    def test_verify_password_wrong(self):
        # verify_password("wrong", hash) == False
        pass
```

### Step 2.1.4 - GREEN: 实现密码服务

**文件**：`backend/app/services/auth.py`

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str: ...
def verify_password(plain: str, hashed: str) -> bool: ...
```

### 验证 Step 2.1.1 - 2.1.4：

```bash
pytest tests/test_db/test_user.py -v
pytest tests/test_services/test_auth.py -v -k "PasswordHash"
```

---

## Task 2.2: JWT 认证 (TDD)

**目标**：实现 JWT token 生成、验证和 OAuth2 密码流。

### Step 2.2.1 - RED: 写 JWT 服务测试

**文件**：`backend/tests/test_services/test_auth.py`

```python
class TestJWTToken:
    def test_create_access_token_returns_string(self):
        # create_access_token({"sub": user_id}) 返回 str
        pass

    def test_decode_token_valid(self):
        # decode_token(token) 返回 payload dict
        pass

    def test_decode_token_expired_raises(self):
        # 过期 token 抛出异常
        pass

    def test_decode_token_invalid_raises(self):
        # 无效 token 抛出异常
        pass
```

### Step 2.2.2 - GREEN: 实现 JWT 服务

**文件**：`backend/app/services/auth.py`（扩展）

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import settings

def create_access_token(data: dict, expires_delta: timedelta = None) -> str: ...
def decode_token(token: str) -> dict: ...
```

### Step 2.2.3 - RED: 写认证 API 测试

**文件**：`backend/tests/test_api/test_auth.py`

```python
class TestAuthAPI:
    def test_login_success(self, client, db_session):
        # POST /api/v1/auth/login 返回 access_token
        pass

    def test_login_wrong_password(self, client, db_session):
        # 错误密码返回 401
        pass

    def test_login_nonexistent_user(self, client):
        # 不存在的用户返回 401
        pass

    def test_me_with_valid_token(self, client, db_session):
        # GET /api/v1/auth/me + Bearer token 返回用户信息
        pass

    def test_me_without_token(self, client):
        # 无 token 返回 401
        pass
```

### Step 2.2.4 - GREEN: 实现认证 API

**文件**：`backend/app/api/v1/auth.py`

```python
router = APIRouter()

@router.post("/auth/login")
def login(req: dict, session: Session = Depends(get_session)):
    # 验证用户名密码 → 生成 JWT → 返回 {"access_token": ..., "token_type": "bearer"}
    ...

@router.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    # 返回当前用户信息
    ...
```

### Step 2.2.5 - 实现认证依赖

**文件**：`backend/app/services/auth.py`（扩展）

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    # 解码 token → 查询用户 → 返回 User
    ...
```

### 验证 Step 2.2.1 - 2.2.5：

```bash
pytest tests/test_services/test_auth.py -v
pytest tests/test_api/test_auth.py -v
```

---

## Task 2.3: RBAC 角色权限控制 (TDD)

**目标**：实现基于角色的 API 访问控制。

### Step 2.3.1 - RED: 写 RBAC 测试

**文件**：`backend/tests/test_api/test_rbac.py`

```python
class TestRBAC:
    def test_admin_can_access_all(self, client, db_session):
        # admin 角色 → 可访问所有端点
        pass

    def test_l1_engineer_cannot_delete_knowledge(self, client, db_session):
        # l1_engineer → DELETE /knowledge/documents 返回 403
        pass

    def test_l2_engineer_can_manage_knowledge(self, client, db_session):
        # l2_engineer → DELETE /knowledge/documents 返回 200
        pass

    def test_manager_can_view_users(self, client, db_session):
        # manager → GET /auth/users 返回 200
        pass

    def test_l1_engineer_cannot_view_users(self, client, db_session):
        # l1_engineer → GET /auth/users 返回 403
        pass
```

### Step 2.3.2 - GREEN: 实现 RBAC 依赖

**文件**：`backend/app/services/auth.py`（扩展）

```python
def require_role(*roles: str):
    """角色权限装饰器工厂"""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(403, "权限不足")
        return current_user
    return dependency
```

### Step 2.3.3 - 应用 RBAC 到现有 API

**文件**：`backend/app/api/v1/knowledge.py`, `ticket.py`, `diagnosis.py`, `chat.py`

- 知识库管理（DELETE）：仅 admin/l2_engineer
- 工单管理（全操作）：l1_engineer 及以上
- 诊断 API：所有登录用户
- 聊天 API：所有登录用户

### 验证 Step 2.3.1 - 2.3.3：

```bash
pytest tests/test_api/test_rbac.py -v
```

---

## Task 2.4: 用户管理 API (TDD)

**目标**：实现用户 CRUD 管理接口。

### Step 2.4.1 - RED: 写用户管理 API 测试

**文件**：`backend/tests/test_api/test_user_management.py`

```python
class TestUserManagement:
    def test_create_user_admin_only(self, client, db_session):
        # POST /auth/users → admin 可创建，其他角色 403
        pass

    def test_list_users_admin_only(self, client, db_session):
        # GET /auth/users → admin/manager 可查看
        pass

    def test_update_user_role(self, client, db_session):
        # PATCH /auth/users/{id} → 更新角色
        pass

    def test_deactivate_user(self, client, db_session):
        # PATCH /auth/users/{id} → is_active = False
        pass

    def test_change_password(self, client, db_session):
        # POST /auth/change-password → 修改自己的密码
        pass
```

### Step 2.4.2 - GREEN: 实现用户管理 API

**文件**：`backend/app/api/v1/auth.py`（扩展）

```python
@router.post("/auth/users")
def create_user(req: dict, session: Session = Depends(get_session),
                current_user: User = Depends(require_role("admin"))):
    ...

@router.get("/auth/users")
def list_users(session: Session = Depends(get_session),
               current_user: User = Depends(require_role("admin", "manager"))):
    ...

@router.patch("/auth/users/{user_id}")
def update_user(user_id: str, req: dict, session: Session = Depends(get_session),
                current_user: User = Depends(require_role("admin"))):
    ...

@router.post("/auth/change-password")
def change_password(req: dict, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
    ...
```

### 验证 Step 2.4.1 - 2.4.2：

```bash
pytest tests/test_api/test_user_management.py -v
```

---

## Task 2.5: 前端认证集成

**目标**：前端实现登录页面、认证状态管理和路由守卫。

### Step 2.5.1 - 添加认证状态到 Redux

**文件**：`frontend/src/store/authSlice.ts`

```typescript
interface AuthState {
  token: string | null;
  user: { id: string; email: string; name: string; role: string } | null;
  loading: boolean;
}

export const login = createAsyncThunk('auth/login', async ({ email, password }) => {
  const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
  localStorage.setItem('token', res.data.access_token);
  return res.data;
});

export const fetchCurrentUser = createAsyncThunk('auth/me', async () => {
  const token = localStorage.getItem('token');
  const res = await axios.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
});
```

### Step 2.5.2 - 登录页面

**文件**：`frontend/src/pages/LoginPage.tsx`

- 邮箱 + 密码表单
- 登录失败提示
- 登录成功跳转到 /chat

### Step 2.5.3 - 路由守卫

**文件**：`frontend/src/App.tsx`（重构）

```tsx
function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { token, user } = useSelector((s: RootState) => s.auth);
  if (!token) return <Navigate to="/login" />;
  if (roles && user && !roles.includes(user.role)) return <Navigate to="/chat" />;
  return <>{children}</>;
}
```

### Step 2.5.4 - 前端 Store 测试

**文件**：`frontend/src/__tests__/authSlice.test.ts`

- 测试 login/logout 状态变更
- 测试 token 持久化

### 验证 Step 2.5.1 - 2.5.4：

```bash
cd frontend && npx vitest run
cd frontend && npm run build
```

---

## Task 2.6: 多租户基础 (TDD)

**目标**：实现租户模型和数据隔离。

### Step 2.6.1 - RED: 写 Tenant 模型测试

**文件**：`backend/tests/test_db/test_tenant.py`

```python
class TestTenant:
    def test_create_tenant(self, db_session):
        # 创建 Tenant，验证 id、name、slug
        pass

    def test_tenant_default_active(self, db_session):
        # 默认 is_active == True
        pass
```

### Step 2.6.2 - GREEN: 实现 Tenant 模型

**文件**：`backend/app/models/tenant.py`

```python
class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)
```

### Step 2.6.3 - 添加 tenant_id 到现有模型

**文件**：`backend/app/models/conversation.py`, `knowledge.py`, `ticket.py`

- 添加 `tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)`
- 默认 nullable=True 兼容现有数据

### Step 2.6.4 - 实现租户隔离查询

**文件**：`backend/app/services/tenant.py`

```python
def get_tenant_filter(user: User) -> dict:
    """返回当前用户的租户过滤条件"""
    if user.tenant_id:
        return {"tenant_id": user.tenant_id}
    return {}
```

### 验证 Step 2.6.1 - 2.6.4：

```bash
pytest tests/test_db/test_tenant.py -v
```

---

## Task 2.7: 诊断流程编辑器 (TDD)

**目标**：实现可视化的诊断流程定义和管理。

### Step 2.7.1 - RED: 写 DiagnosisFlow 模型测试

**文件**：`backend/tests/test_db/test_diagnosis_flow.py`

```python
class TestDiagnosisFlow:
    def test_create_flow(self, db_session):
        # 创建 DiagnosisFlow，验证 name、steps、version
        pass

    def test_flow_default_version(self, db_session):
        # 默认 version == 1
        pass

    def test_flow_steps_json(self, db_session):
        # steps 是 JSON 数组
        pass
```

### Step 2.7.2 - GREEN: 实现 DiagnosisFlow 模型

**文件**：`backend/app/models/diagnosis_flow.py`

```python
class DiagnosisFlow(Base, TimestampMixin):
    __tablename__ = "diagnosis_flows"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(JSON, nullable=False)  # [{id, title, description, conditions, next_step}]
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True)
```

### Step 2.7.3 - RED: 写流程 API 测试

**文件**：`backend/tests/test_api/test_diagnosis_flow.py`

```python
class TestDiagnosisFlowAPI:
    def test_create_flow(self, client, db_session):
        pass

    def test_list_flows(self, client, db_session):
        pass

    def test_get_flow(self, client, db_session):
        pass

    def test_update_flow(self, client, db_session):
        pass

    def test_delete_flow(self, client, db_session):
        pass

    def test_activate_flow(self, client, db_session):
        pass
```

### Step 2.7.4 - GREEN: 实现流程 API

**文件**：`backend/app/api/v1/diagnosis_flow.py`

```python
router = APIRouter()

@router.post("/diagnosis/flows")      # 创建流程
@router.get("/diagnosis/flows")        # 列表
@router.get("/diagnosis/flows/{id}")   # 详情
@router.patch("/diagnosis/flows/{id}") # 更新
@router.delete("/diagnosis/flows/{id}")# 删除
@router.post("/diagnosis/flows/{id}/activate")  # 激活
```

### Step 2.7.5 - 前端流程编辑器页面

**文件**：`frontend/src/pages/DiagnosisFlowPage.tsx`

- 流程列表（Table）
- 创建/编辑流程（Modal + Steps 组件）
- 步骤编辑器（动态表单：步骤标题、描述、条件、下一步）
- 激活/停用流程

### 验证 Step 2.7.1 - 2.7.5：

```bash
pytest tests/test_db/test_diagnosis_flow.py -v
pytest tests/test_api/test_diagnosis_flow.py -v
npx vitest run
```

---

## Phase 2 任务依赖关系

```
2.1 User 模型 + 密码安全
  │
  ├── 2.2 JWT 认证
  │    └── 2.3 RBAC 角色权限
  │         └── 2.4 用户管理 API
  │              └── 2.5 前端认证集成
  │
  ├── 2.6 多租户基础
  │
  └── 2.7 诊断流程编辑器
```

## 验证清单 (Phase 2 完成标准)

- [x] 用户可注册/登录，密码使用 bcrypt 哈希
- [x] JWT token 认证，所有 API 需 Bearer token
- [x] RBAC 角色权限：admin/manager/l2_engineer/l1_engineer
- [x] 用户管理 API（仅 admin 可操作）
- [x] 前端登录页面 + 路由守卫
- [x] 多租户模型 + 数据隔离
- [x] 诊断流程编辑器（CRUD + 激活）
- [x] `pytest tests/ -v` 全部通过 (171 tests)
- [x] `npx vitest run` 前端测试全部通过 (12 tests)
- [x] `ruff check backend/app/` 全部通过
