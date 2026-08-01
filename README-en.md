# 🤖 Tech Support Assistant / 技术支持助手

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-4B0082.svg)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![Test](https://img.shields.io/badge/tests-233%20passed-brightgreen.svg)](#testing)
[![TDD](https://img.shields.io/badge/TDD-driven-red.svg)](#development-guidelines)

> Enterprise AI Agent Platform for Technical Support Teams

**[简体中文](README-zh.md)** · [Back to main](README.md)

---

### 📖 Introduction

**Tech Support Assistant** is an enterprise AI Agent platform designed for internal technical support teams. It leverages AI automation to help support engineers resolve customer issues more efficiently.

### ✨ Key Features

| Feature                                | Description                                                                |
| -------------------------------------- | -------------------------------------------------------------------------- |
| 🔍 **Intelligent Knowledge Retrieval** | RAG-based Q&A with vector search, cosine similarity and citations          |
| 📝 **Text Chunking**                   | Intelligent chunking with paragraph-level splitting and overlap            |
| 🩺 **AI-Powered Diagnosis**            | AI-driven fault diagnosis with pattern matching and LLM suggestions        |
| 📋 **Ticket Management**               | Create, query, update tickets with priority and status management          |
| 📊 **Data Analytics**                  | Query conversation, message, and knowledge base statistics                 |
| ⚠️ **Smart Escalation**                | Auto-identify critical issues, create escalation tickets and notify        |
| 🤝 **Human-in-the-Loop**               | Manual approval required for high-risk escalation, approve/reject          |
| 🔐 **Authentication & Authorization**  | JWT auth + OAuth2 password flow, bcrypt hashing, RBAC role-based access    |
| 🏢 **Multi-Tenancy**                   | Tenant model + data isolation for multi-organization support               |
| 🔄 **Diagnosis Flow Editor**           | Visual diagnosis flow definition with CRUD, versioning, and activation     |
| 🤖 **Multi-Agent Collaboration**       | Supervisor Agent routes intent to specialized sub-agents                   |
| 💬 **SSE Streaming Chat**              | Real-time streaming responses with citation source display                 |
| 📚 **Knowledge Base Management**       | Document upload, chunking, vectorization with full CRUD                    |
| 🖥️ **React Frontend**                  | Complete chat/diagnosis/ticket/knowledge/login interface with route guards |
| 🏥 **Health Check**                    | API health monitoring for quick service diagnostics                        |
| 🧪 **TDD-Driven**                      | Complete test suite covering Agents, APIs, DB, Services                    |

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client Layer                         │
│            Web UI (React + TypeScript)                   │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    FastAPI Service Layer                  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           LangGraph Agent Orchestrator             │ │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────┐  │ │
│  │  │ Supervisor │  │  Knowledge │  │  Diagnosis  │  │ │
│  │  │   Agent    │  │   Agent    │  │    Agent    │  │ │
│  │  └────────────┘  └────────────┘  └─────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ LLMRouter  │  │Knowledge   │  │  Session Manager │  │
│  │            │  │  Service   │  │                  │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                     Data Layer                            │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL │  │  SQLite    │  │ pgvector (Vector) │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 🛠️ Tech Stack

#### Backend

- **Python 3.12+** - Primary language
- **FastAPI 0.115+** - Modern web framework
- **SQLAlchemy 2.0+** - ORM
- **LangGraph 0.2+** - AI Agent orchestration
- **PostgreSQL 16+** - Primary database
- **pgvector 0.3+** - Vector search extension
- **Alembic 1.13+** - Database migrations

#### Frontend

- **React 18** - UI framework
- **TypeScript 5** - Type safety
- **Redux Toolkit** - State management
- **Ant Design 5** - UI component library
- **React Router 6** - Routing
- **Axios** - HTTP client

#### Development Tools

- **pytest** - Python testing framework
- **Ruff** - Linting and formatting
- **Husky + lint-staged** - Git hooks
- **Docker** - Containerization

### 📁 Project Structure

```
technical-support-assistant/
├── backend/                              # Backend Application
│   ├── app/
│   │   ├── agents/                       # AI Agent definitions
│   │   │   ├── supervisor.py            #   Supervisor Agent
│   │   │   ├── diagnosis.py             #   Diagnosis Agent
│   │   │   ├── ticket_agent.py          #   Ticket Agent
│   │   │   ├── data.py                  #   Data Analytics Agent
│   │   │   └── escalation.py            #   Escalation Agent
│   │   ├── api/                          # API routes
│   │   │   └── v1/
│   │   │       ├── chat.py              #   Chat API
│   │   │       ├── health.py           #   Health check
│   │   │       ├── knowledge.py        #   Knowledge API
│   │   │       ├── diagnosis.py         #   Diagnosis API
│   │   │       ├── ticket.py            #   Ticket API
│   │   │       ├── auth.py              #   Auth API
│   │   │       ├── external.py          #   External integration API
│   │   │       ├── notification.py      #   IM notification API
│   │   │       └── admin.py             #   Admin API
│   │   ├── core/                         # Core configuration
│   │   │   └── config.py               #   Global settings
│   │   ├── db/                           # Database layer
│   │   │   ├── base.py                 #   Base models
│   │   │   ├── guid.py                 #   UUID utility
│   │   │   └── session.py             #   Session management
│   │   ├── models/                       # Data models
│   │   │   ├── conversation.py         #   Conversation model
│   │   │   ├── knowledge.py           #   Knowledge model
│   │   │   ├── error_pattern.py        #   Error pattern model
│   │   │   ├── ticket.py               #   Ticket model
│   │   │   ├── user.py                 #   User model
│   │   │   ├── tenant.py               #   Tenant model
│   │   │   ├── diagnosis_flow.py       #   Diagnosis flow model
│   │   │   └── audit_log.py            #   Audit log model
│   │   ├── services/                     # Business services
│   │   │   ├── knowledge.py            #   Knowledge service
│   │   │   ├── llm.py                  #   LLM router
│   │   │   ├── llm_fallback.py         #   Multi-model fallback
│   │   │   ├── chunking.py             #   Text chunking
│   │   │   ├── rag.py                  #   RAG retrieval
│   │   │   ├── diagnosis.py            #   Error diagnosis
│   │   │   ├── ticket.py               #   Ticket service
│   │   │   ├── data_query.py           #   Data query service
│   │   │   ├── auth.py                 #   Auth service
│   │   │   ├── tenant.py               #   Tenant isolation service
│   │   │   ├── audit.py                #   Audit log service
│   │   │   ├── external_ticket.py      #   External ticket integration
│   │   │   ├── notification.py         #   IM notification service
│   │   │   ├── quality_eval.py         #   Quality evaluation service
│   │   │   └── knowledge_discovery.py  #   Knowledge auto-discovery
│   │   ├── main.py                       #   Application entry
│   │   └── ...
│   ├── tests/                            # Test suite
│   │   ├── conftest.py                  #   Global fixtures
│   │   ├── mock_providers.py            #   Mock providers
│   │   ├── test_agents/                 #   Agent tests
│   │   ├── test_api/                    #   API tests
│   │   ├── test_db/                     #   Database tests
│   │   └── test_services/              #   Service tests
│   ├── alembic/                          # Database migrations
│   └── pyproject.toml                   # Project config
├── frontend/                             # Frontend Application
│   ├── src/
│   │   ├── pages/                        #   Page components
│   │   │   ├── ChatPage.tsx            #     Chat page
│   │   │   ├── DiagnosisPage.tsx       #     Fault diagnosis page
│   │   │   ├── TicketPage.tsx          #     Ticket management page
│   │   │   ├── KnowledgeBasePage.tsx  #     Knowledge base management
│   │   │   ├── LoginPage.tsx           #     Login page
│   │   │   ├── DashboardPage.tsx       #     Dashboard
│   │   │   ├── UserManagementPage.tsx  #     User management
│   │   │   ├── IntegrationPage.tsx     #     Integration management
│   │   │   ├── KnowledgeDiscoveryPage.tsx #  Knowledge discovery
│   │   │   └── DiagnosisFlowPage.tsx   #     Diagnosis flow editor
│   │   ├── services/                     #   API services
│   │   ├── store/                        #   Redux Store
│   │   ├── hooks/                        #   Custom Hooks
│   │   ├── __tests__/                    #   Frontend tests
│   │   ├── App.tsx                       #   Root component
│   │   └── main.tsx                      #   Entry point
│   └── package.json                      #   Frontend config
├── .husky/                               # Git hooks
├── SPEC.md                               # Technical specification
├── PRD.md                                # Product requirement doc
├── design.md                             # Architecture design
├── plan.md                               # Implementation plan
└── README.md                             # Project documentation
```

### 🚀 Quick Start

#### Prerequisites

| Component  | Minimum Version |
| ---------- | --------------- |
| Python     | 3.12            |
| PostgreSQL | 16              |
| Node.js    | 20              |
| Git        | 2.40            |

#### Installation

**1. Clone the repository**

```bash
git clone <repository-url>
cd technical-support-assistant
```

**2. Install backend dependencies**

```bash
cd backend
pip install -e ".[dev]"
```

**3. Configure environment**

```bash
# Create .env file in backend directory
cp .env.example .env

# Edit .env with your settings
DB_DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/tech_support
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
```

**4. Initialize database**

```bash
# Start PostgreSQL (using Docker)
docker run -d \
  --name tech-support-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=tech_support \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Run database migrations
cd backend
alembic upgrade head
```

**5. Start development server**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**6. Verify service**

```bash
# Check health status
curl http://localhost:8000/api/v1/health
# Returns: {"status":"ok","version":"0.1.0"}
```

### 📡 API Documentation

After starting the server, visit Swagger UI: `http://localhost:8000/docs`

#### API Endpoints

| Method             | Path                                         | Description                                         |
| ------------------ | -------------------------------------------- | --------------------------------------------------- |
| **Health**         |                                              |                                                     |
| GET                | `/api/v1/health`                             | Service health check                                |
| **Conversations**  |                                              |                                                     |
| GET                | `/api/v1/chat/conversations`                 | List conversations                                  |
| POST               | `/api/v1/chat/conversations`                 | Create new conversation                             |
| GET                | `/api/v1/chat/conversations/{id}`            | Get conversation details                            |
| DELETE             | `/api/v1/chat/conversations/{id}`            | Delete conversation                                 |
| GET                | `/api/v1/chat/conversations/{id}/messages`   | Get conversation messages                           |
| **Chat**           |                                              |                                                     |
| POST               | `/api/v1/chat/completions`                   | Send message (SSE streaming)                        |
| POST               | `/api/v1/chat/completions/resume`            | Resume interrupted chat (approve/reject escalation) |
| **Knowledge Base** |                                              |                                                     |
| POST               | `/api/v1/knowledge/documents`                | Upload document                                     |
| GET                | `/api/v1/knowledge/documents`                | List documents                                      |
| GET                | `/api/v1/knowledge/documents/{id}`           | Get document details                                |
| DELETE             | `/api/v1/knowledge/documents/{id}`           | Delete document                                     |
| POST               | `/api/v1/knowledge/search`                   | Search knowledge base                               |
| **Auth**           |                                              |                                                     |
| POST               | `/api/v1/auth/login`                         | User login (returns JWT)                            |
| GET                | `/api/v1/auth/me`                            | Get current user info                               |
| POST               | `/api/v1/auth/users`                         | Create user (admin only)                            |
| GET                | `/api/v1/auth/users`                         | List users (admin/manager)                          |
| PATCH              | `/api/v1/auth/users/{id}`                    | Update user (admin only)                            |
| DELETE             | `/api/v1/auth/users/{id}`                    | Delete user (admin only)                            |
| POST               | `/api/v1/auth/change-password`               | Change password                                     |
| **Diagnosis Flow** |                                              |                                                     |
| POST               | `/api/v1/diagnosis/flows`                    | Create diagnosis flow                               |
| GET                | `/api/v1/diagnosis/flows`                    | List flows                                          |
| GET                | `/api/v1/diagnosis/flows/{id}`               | Get flow details                                    |
| PATCH              | `/api/v1/diagnosis/flows/{id}`               | Update flow                                         |
| DELETE             | `/api/v1/diagnosis/flows/{id}`               | Delete flow                                         |
| POST               | `/api/v1/diagnosis/flows/{id}/activate`      | Activate flow                                       |
| **External**       |                                              |                                                     |
| POST               | `/api/v1/external/tickets/sync`              | Sync ticket to external system                      |
| GET                | `/api/v1/external/tickets/config/{provider}` | Get external system config                          |
| **Notification**   |                                              |                                                     |
| POST               | `/api/v1/notification/send`                  | Send IM notification                                |
| POST               | `/api/v1/notification/escalation`            | Send escalation notification                        |
| **Admin**          |                                              |                                                     |
| GET                | `/api/v1/admin/stats`                        | System statistics                                   |
| POST               | `/api/v1/admin/quality/evaluate`             | Quality evaluation                                  |
| POST               | `/api/v1/admin/knowledge/discover`           | Knowledge auto-discovery                            |

#### Request Examples

**Send chat message**

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "content": "How to configure SSL certificates?",
    "conversation_id": "optional, omit for new conversation"
  }'
```

**Upload knowledge document**

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/documents \
  -F "title=SSL Configuration Guide" \
  -F "file=@ssl-guide.md"
```

**Search knowledge base**

```bash
curl "http://localhost:8000/api/v1/knowledge/search?query=SSL&top_k=5"
```

**Resume interrupted chat (approve escalation)**

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions/resume \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-uuid",
    "approved": true
  }'
```

**Resume interrupted chat (reject escalation)**

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions/resume \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-uuid",
    "approved": false
  }'
```

### Testing

#### Run All Tests

```bash
cd backend
pytest tests/ -v
```

#### Test Categories

| Type           | Path                           | Description                     |
| -------------- | ------------------------------ | ------------------------------- |
| Agent Tests    | `tests/test_agents/`           | Supervisor Agent intent routing |
| API Tests      | `tests/test_api/`              | Chat, knowledge, and auth APIs  |
| Database Tests | `tests/test_db/`               | Data models and sessions        |
| Service Tests  | `tests/test_services/`         | LLM router, knowledge, tenant   |
| Config Tests   | `tests/test_config.py`         | Environment configuration       |
| Mock Tests     | `tests/test_mock_providers.py` | Mock providers                  |

#### Test Coverage

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Development Guidelines

#### TDD Workflow

This project follows **TDD (Test-Driven Development)**:

```
1. RED: Write test → Run and confirm failure
2. GREEN: Write minimal implementation → Run tests and pass
3. REFACTOR: Optimize code → Tests still pass
```

#### Commit Convention

Following [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

**Example**:

```
feat(chat): Implement SSE streaming response

- Implement Supervisor Agent based on LangGraph
- Support knowledge retrieval and intent routing
- Add conversation management API

Closes #12
```

#### Git Hooks

- **pre-commit**: Automatically runs `ruff check` + `ruff format`
- **commit-msg**: Validates commit message format

### Docker Deployment

#### Using Docker Compose

```bash
# Start all services (PostgreSQL + Backend + Frontend)
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f backend
```

#### Services

| Service     | Port | Description                           |
| ----------- | ---- | ------------------------------------- |
| PostgreSQL  | 5432 | Main database with pgvector extension |
| Backend API | 8000 | FastAPI backend service               |
| Frontend    | 3000 | React frontend (development mode)     |

#### Environment Configuration

Create a `.env` file at the project root:

```env
# LLM API Key (required)
LLM_API_KEY=your-openai-api-key

# Optional configurations
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1

# JWT Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### Environment Variables

| Variable               | Description          | Default                                                            |
| ---------------------- | -------------------- | ------------------------------------------------------------------ |
| `APP_NAME`             | Application name     | Tech Support Assistant                                             |
| `DEBUG`                | Debug mode           | false                                                              |
| `DB_DSN`               | Database connection  | postgresql+asyncpg://postgres:postgres@localhost:5432/tech_support |
| `LLM_PROVIDER`         | LLM provider         | openai                                                             |
| `LLM_API_KEY`          | LLM API Key          | (required)                                                         |
| `LLM_BASE_URL`         | LLM API endpoint     | https://api.openai.com/v1                                          |
| `LLM_MODEL`            | LLM model            | gpt-4o-mini                                                        |
| `EMBEDDING_PROVIDER`   | Embedding provider   | openai                                                             |
| `EMBEDDING_MODEL`      | Embedding model      | text-embedding-3-small                                             |
| `EMBEDDING_DIMENSIONS` | Embedding dimensions | 1536                                                               |
| `JWT_SECRET_KEY`       | JWT secret key       | (required)                                                         |
| `JWT_ALGORITHM`        | JWT algorithm        | HS256                                                              |
| `JWT_EXPIRE_MINUTES`   | JWT expiration       | 1440                                                               |

### Related Documentation

| Document               | Description                    |
| ---------------------- | ------------------------------ |
| [PRD.md](PRD.md)       | Product Requirements Document  |
| [design.md](design.md) | Architecture Design Document   |
| [plan.md](plan.md)     | Implementation Plan            |
| [SPEC.md](SPEC.md)     | Technical Specification        |
| [AGENTS.md](AGENTS.md) | Agent architecture and testing |

### License

This project is licensed under the [MIT License](LICENSE).
