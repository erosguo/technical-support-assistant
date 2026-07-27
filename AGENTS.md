# AGENTS.md — Tech Support Assistant

## Quick start

```bash
cd backend
pip install -e ".[dev]"
# .env file at backend/.env (DB_DSN, LLM_API_KEY, LLM_MODEL)
uvicorn app.main:app --reload --port 8000
```

## Test commands

```bash
cd backend
pytest tests/ -v                              # all 37 tests
pytest tests/test_api/ -v                     # API integration tests only
pytest tests/ --cov=app --cov-report=term-missing  # coverage
```

## Non-obvious architecture

- **Sync SQLAlchemy for MVP** — async engine (`greenlet` DLL) fails on Windows. DB DSN is `postgresql+asyncpg://...` but `session.py` strips it to `postgresql://` at runtime.
- **SQLite for testing, PostgreSQL for production.** Custom `GUID` type (`app/db/guid.py`) stores as `String(36)` on SQLite, native `UUID` on PostgreSQL. All tests use SQLite.
- **LangGraph agent runs inside sync routes** via `asyncio.run()`. SSE streaming uses `StreamingResponse` with a sync generator.
- **LLM mocking**: `MockLLMProvider` in `tests/mock_providers.py` matches user message content by substring against a response dict. Never calls an external API.
- **Alembic** configured for async PostgreSQL but cannot run migrations locally (no PostgreSQL available). Tables created/dropped in tests via `Base.metadata.create_all/drop_all`.

## Test infrastructure quirks

| Quirk                      | Detail                                                                                     |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| `conftest.py`              | Creates all tables, drops after test session. Auto-rollback per `db_session` fixture.      |
| `test_api/conftest.py`     | Overrides FastAPI `get_session` dependency. Uses `httpx.AsyncClient` with `ASGITransport`. |
| `client.aclose()`          | Needs `asyncio.run(client.aclose())` because test runs in sync context.                    |
| UUID in SQLite             | `session.get(Model, string_id)` works because `GUID` type returns `str` on SQLite.         |
| `build_supervisor_graph()` | Accepts optional `LLMRouter` for mock injection.                                           |

## Pre-commit & linting (root-level)

- `npm install` sets up husky hooks.
- `pre-commit` → `npx lint-staged` → `ruff check` + `ruff format` on `*.py`, `prettier --write` on `*.{json,md}`.
- `commit-msg` → `npx commitlint --edit` (Conventional Commits).
- Manual lint: `ruff check backend/app/` from root.
- `backend/pyproject.toml` is the source of truth for Python lint/format config.

## Project layout

```
backend/app/main.py          # FastAPI entrypoint
backend/app/agents/           # LangGraph agents (only supervisor.py so far)
backend/app/api/v1/           # health, chat, knowledge routers
backend/app/db/               # base.py, session.py, guid.py
backend/app/models/           # Conversation, Message, KnowledgeDocument, DocumentChunk
backend/app/services/         # LLMRouter + OpenAIProvider, knowledge service
backend/tests/conftest.py     # test DB + mock_llm fixture
backend/tests/mock_providers.py
backend/alembic/              # migrations (async, needs PostgreSQL)
frontend/src/                 # skeleton only (empty types/, __tests__/, store/)
```

## Key conventions

- **TDD**: Red → Green → Refactor. Never commit code whose tests fail.
- **Conventional Commits**: `feat(scope): msg`, with types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- **PEP 8**, 120-char line width, ruff for lint+format, no `ruff.toml` (config in `pyproject.toml`).
- All models have `id` (UUID/GUID), `created_at`, `updated_at` (via `TimestampMixin`).
- API prefix: `/api/v1/`.
