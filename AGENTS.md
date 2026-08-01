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
pytest tests/ -v                              # all 125 tests
pytest tests/test_api/ -v                     # API integration tests only
pytest tests/ --cov=app --cov-report=term-missing  # coverage
```

## Non-obvious architecture

- **Sync SQLAlchemy for MVP** — async engine (`greenlet` DLL) fails on Windows. DB DSN is `postgresql+asyncpg://...` but `session.py` strips it to `postgresql://` at runtime.
- **SQLite for testing, PostgreSQL for production.** Custom `GUID` type (`app/db/guid.py`) stores as `String(36)` on SQLite, native `UUID` on PostgreSQL. All tests use SQLite.
- **LangGraph agent runs inside sync routes** via `asyncio.run()`. SSE streaming uses `StreamingResponse` with a sync generator.
- **LLM mocking**: `MockLLMProvider` in `tests/mock_providers.py` matches user message content by substring against a response dict. Never calls an external API.
- **Alembic** configured for async PostgreSQL but cannot run migrations locally (no PostgreSQL available). Tables created/dropped in tests via `Base.metadata.create_all/drop_all`.
- **Human-in-the-loop** uses LangGraph `interrupt()` (`langgraph.types`) + `MemorySaver` checkpointer. Module-level checkpointer in `chat.py` keyed by conversation_id (`thread_id`). Resume builds a FRESH graph with the same checkpointer + current session — the DB session cannot be serialized, so don't reuse the old graph object.
- **Multi-agent flow**: `detect_intent → diagnosis → escalation → human_approval (interrupt) → ticket`. Conditional edges (`diagnosis_router`, `escalation_router`, `human_approval_router`) chain these. Ticket creation happens in `ticket_node` when it sees `escalation.escalated` context.
- **Chat state** must set `error_info` to the user content — an empty string overrides `diagnosis_node`'s `state.get("error_info", last_message)` fallback and silently disables pattern matching.

## Test infrastructure quirks

| Quirk                      | Detail                                                                                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `conftest.py`              | Creates all tables, drops after test session. Auto-rollback per `db_session` fixture.                                                                                    |
| `test_api/conftest.py`     | Overrides FastAPI `get_session` dependency. Uses `httpx.AsyncClient` with `ASGITransport`.                                                                               |
| `client.aclose()`          | Needs `asyncio.run(client.aclose())` because test runs in sync context.                                                                                                  |
| UUID in SQLite             | `session.get(Model, string_id)` works because `GUID` type returns `str` on SQLite.                                                                                       |
| `build_supervisor_graph()` | Accepts optional `LLMRouter`, `Session`, and `checkpointer`. Mock LLM via `patch("app.agents.supervisor.LLMRouter")`.                                                    |
| Batch insert + GUID        | `session.add_all([...]) + commit()` fails on SQLite (`insertmanyvalues` sentinel KeyError). Insert one-at-a-time with `flush()` between.                                 |
| interrupt tests            | Need `MemorySaver` checkpointer + `Command(resume=...)` + unique `thread_id` per test. Without a checkpointer, `interrupt()` silently skips and blocks downstream nodes. |
| chat API tests             | Must `patch("app.api.v1.chat.LLMRouter")` AND `patch("app.agents.supervisor.LLMRouter")` or the real LLM is hit.                                                         |

## Pre-commit & linting (root-level)

- `npm install` sets up husky hooks.
- `pre-commit` → `npx lint-staged` → `ruff check` + `ruff format` on `*.py`, `prettier --write` on `*.{json,md}`.
- `commit-msg` → `npx commitlint --edit` (Conventional Commits).
- Manual lint: `ruff check backend/app/` from root.
- `backend/pyproject.toml` is the source of truth for Python lint/format config.

## Project layout

```
backend/app/main.py          # FastAPI entrypoint
backend/app/agents/           # supervisor + diagnosis/ticket/data/escalation nodes
backend/app/api/v1/           # health, chat, knowledge, diagnosis, ticket routers
backend/app/db/               # base.py, session.py, guid.py
backend/app/models/           # Conversation, Message, KnowledgeDocument, DocumentChunk, ErrorPattern, Ticket
backend/app/services/         # LLMRouter, knowledge, diagnosis, ticket, data_query services
backend/tests/conftest.py     # test DB + mock_llm fixture
backend/tests/mock_providers.py
backend/alembic/              # migrations (async, needs PostgreSQL)
frontend/src/                 # ChatPage (with approval modal), DiagnosisPage, KnowledgeBasePage, TicketPage
```

## Key conventions

- **TDD**: Red → Green → Refactor. Never commit code whose tests fail.
- **Conventional Commits**: `feat(scope): msg`, with types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- **PEP 8**, 120-char line width, ruff for lint+format, no `ruff.toml` (config in `pyproject.toml`).
- All models have `id` (UUID/GUID), `created_at`, `updated_at` (via `TimestampMixin`).
- API prefix: `/api/v1/`.
