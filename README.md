# 🤖 技术支持助手 / Tech Support Assistant

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-4B0082.svg)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![Test](https://img.shields.io/badge/tests-37%20passed-brightgreen.svg)](#测试)
[![TDD](https://img.shields.io/badge/TDD-driven-red.svg)](#开发规范)

> 面向内部技术支持团队的企业级 AI Agent 平台  
> Enterprise AI Agent Platform for Technical Support Teams

[简体中文](#简体中文) · [English](#english)

---

## 简体中文

### 📖 项目简介

**技术支持助手** 是一个面向企业内部技术支持团队的 AI Agent 平台，旨在通过 AI 自动化和智能化手段，帮助技术支持工程师更高效地解决客户问题。

### ✨ 核心特性

| 特性                 | 说明                                                          |
| -------------------- | ------------------------------------------------------------- |
| 🔍 **智能知识检索**  | 基于 RAG 的知识库问答，支持向量检索、余弦相似度匹配和引用溯源 |
| 📝 **文本分块**      | 智能分块算法，支持段落级分块和重叠窗口，优化上下文检索        |
| 🩺 **故障诊断**      | AI 驱动的故障诊断，结合模式匹配和 LLM 生成诊断建议            |
| 📋 **工单管理**      | 支持工单创建、查询、更新，多优先级和状态管理                  |
| 🤖 **多 Agent 协作** | Supervisor Agent 智能路由用户意图到知识问答或诊断子 Agent     |
| 💬 **SSE 流式对话**  | 服务端推送技术，实现实时流式响应，支持引用来源展示            |
| 📚 **知识库管理**    | 支持文档上传、分块、向量化和搜索，完整的 CRUD 操作            |
| 🖥️ **React 前端**    | 完整的聊天/诊断/知识库界面，支持会话、引用标签、流式加载      |
| 🏥 **健康检查**      | API 健康监控，快速定位服务状态                                |
| 🧪 **TDD 驱动**      | 完整的测试套件，覆盖 Agent、API、数据库、服务层               |

### 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                       客户端层                            │
│              Web UI (React + TypeScript)                 │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    FastAPI 服务层                         │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              LangGraph Agent Orchestrator          │ │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────┐  │ │
│  │  │ Supervisor │  │  Knowledge │  │  Diagnosis  │  │ │
│  │  │   Agent    │  │   Agent    │  │    Agent    │  │ │
│  │  └────────────┘  └────────────┘  └─────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ LLMRouter  │  │ 知识库服务  │  │   会话管理服务    │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                      数据层                               │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL │  │  SQLite    │  │  向量检索(pgvector)│  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 🛠️ 技术栈

#### 后端

- **Python 3.12+** - 主开发语言
- **FastAPI 0.115+** - 现代 Web 框架
- **SQLAlchemy 2.0+** - ORM
- **LangGraph 0.2+** - AI Agent 编排框架
- **PostgreSQL 16+** - 主数据库
- **pgvector 0.3+** - 向量检索扩展
- **Alembic 1.13+** - 数据库迁移

#### 前端

- **React 18** - UI 框架
- **TypeScript 5** - 类型安全
- **Redux Toolkit** - 状态管理
- **Ant Design 5** - UI 组件库
- **React Router 6** - 路由管理
- **Axios** - HTTP 客户端

#### 开发工具

- **pytest** - Python 测试框架
- **Ruff** - 代码检查和格式化
- **Husky + lint-staged** - Git 钩子
- **Docker** - 容器化部署

### 📁 项目结构

```
technical-support-assistant/
├── backend/                              # 后端应用
│   ├── app/
│   │   ├── agents/                       # AI Agent 定义
│   │   │   ├── supervisor.py            #   Supervisor Agent
│   │   │   └── diagnosis.py             #   故障诊断 Agent
│   │   ├── api/                          # API 路由层
│   │   │   └── v1/
│   │   │       ├── chat.py              #   聊天 API
│   │   │       ├── health.py           #   健康检查
│   │   │       ├── knowledge.py        #   知识库 API
│   │   │       └── diagnosis.py         #   诊断 API
│   │   ├── core/                         # 核心配置
│   │   │   └── config.py               #   全局设置
│   │   ├── db/                           # 数据库层
│   │   │   ├── base.py                 #   基础模型
│   │   │   ├── guid.py                 #   UUID 生成
│   │   │   └── session.py             #   会话管理
│   │   ├── models/                       # 数据模型
│   │   │   ├── conversation.py         #   会话模型
│   │   │   ├── knowledge.py           #   知识库模型
│   │   │   ├── error_pattern.py        #   错误模式模型
│   │   │   └── ticket.py               #   工单模型
│   │   ├── services/                     # 业务服务
│   │   │   ├── knowledge.py            #   知识库服务
│   │   │   ├── llm.py                  #   LLM 路由
│   │   │   ├── chunking.py             #   文本分块
│   │   │   ├── rag.py                  #   RAG 检索
│   │   │   ├── diagnosis.py            #   错误诊断
│   │   │   └── ticket.py               #   工单服务
│   │   ├── main.py                       #   应用入口
│   │   └── ...
│   ├── tests/                            # 测试套件
│   │   ├── conftest.py                  #   全局 Fixtures
│   │   ├── mock_providers.py            #   Mock 提供者
│   │   ├── test_agents/                 #   Agent 测试
│   │   │   └── test_diagnosis.py       #     诊断 Agent 测试
│   │   ├── test_api/                    #   API 测试
│   │   │   └── test_diagnosis.py       #     诊断 API 测试
│   │   ├── test_db/                     #   数据库测试
│   │   │   ├── test_error_pattern.py   #     错误模式测试
│   │   │   └── test_ticket.py          #     工单模型测试
│   │   └── test_services/              #   服务测试
│   │       ├── test_diagnosis.py       #     诊断服务测试
│   │       └── test_ticket.py          #     工单服务测试
│   ├── alembic/                          # 数据库迁移
│   └── pyproject.toml                   # 项目配置
├── frontend/                             # 前端应用
│   ├── src/
│   │   ├── pages/                        #   页面组件
│   │   │   ├── ChatPage.tsx            #     聊天页面
│   │   │   ├── DiagnosisPage.tsx       #     故障诊断页面
│   │   │   └── KnowledgeBasePage.tsx  #     知识库管理页面
│   │   ├── services/                     #   API 服务
│   │   │   ├── knowledge.ts            #     知识库 API
│   │   │   └── diagnosis.ts            #     诊断 API
│   │   ├── store/                        #   Redux Store
│   │   │   ├── index.ts               #     Store 配置
│   │   │   └── conversationSlice.ts   #     会话状态
│   │   ├── __tests__/                    #   前端测试
│   │   ├── App.tsx                       #   根组件
│   │   └── main.tsx                      #   入口文件
│   └── package.json                      # 前端配置
├── .husky/                               # Git 钩子
├── SPEC.md                               # 技术规范文档
├── PRD.md                                # 产品需求文档
├── design.md                             # 架构设计文档
├── plan.md                               # 实现计划
└── README.md                             # 项目说明
```

### 🚀 快速开始

#### 环境要求

| 组件       | 最低版本 |
| ---------- | -------- |
| Python     | 3.12     |
| PostgreSQL | 16       |
| Node.js    | 20       |
| Git        | 2.40     |

#### 安装步骤

**1. 克隆仓库**

```bash
git clone <repository-url>
cd technical-support-assistant
```

**2. 安装后端依赖**

```bash
cd backend
pip install -e ".[dev]"
```

**3. 配置环境变量**

```bash
# 在 backend 目录创建 .env 文件
cp .env.example .env

# 编辑 .env 配置以下参数
DB_DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/tech_support
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
```

**4. 初始化数据库**

```bash
# 启动 PostgreSQL (使用 Docker)
docker run -d \
  --name tech-support-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=tech_support \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 运行数据库迁移
cd backend
alembic upgrade head
```

**5. 启动开发服务器**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**6. 验证服务**

```bash
# 检查健康状态
curl http://localhost:8000/api/v1/health
# 返回: {"status":"ok","version":"0.1.0"}
```

### 📡 API 文档

启动服务后访问 Swagger UI：`http://localhost:8000/docs`

#### API 列表

| 方法         | 路径                                       | 说明                 |
| ------------ | ------------------------------------------ | -------------------- |
| **健康检查** |                                            |                      |
| GET          | `/api/v1/health`                           | 服务健康检查         |
| **会话管理** |                                            |                      |
| GET          | `/api/v1/chat/conversations`               | 获取会话列表         |
| POST         | `/api/v1/chat/conversations`               | 创建新会话           |
| GET          | `/api/v1/chat/conversations/{id}`          | 获取会话详情         |
| DELETE       | `/api/v1/chat/conversations/{id}`          | 删除会话             |
| GET          | `/api/v1/chat/conversations/{id}/messages` | 获取会话消息         |
| **聊天对话** |                                            |                      |
| POST         | `/api/v1/chat/completions`                 | 发送消息（SSE 流式） |
| **知识库**   |                                            |                      |
| POST         | `/api/v1/knowledge/documents`              | 上传文档             |
| GET          | `/api/v1/knowledge/documents`              | 文档列表             |
| GET          | `/api/v1/knowledge/documents/{id}`         | 文档详情             |
| DELETE       | `/api/v1/knowledge/documents/{id}`         | 删除文档             |
| POST         | `/api/v1/knowledge/search`                 | 搜索知识库           |

#### 请求示例

**发送聊天消息**

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "content": "如何配置 SSL 证书？",
    "conversation_id": "可选，新对话时不传"
  }'
```

**上传知识文档**

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/documents \
  -F "title=SSL 配置指南" \
  -F "file=@ssl-guide.md"
```

**搜索知识库**

```bash
curl "http://localhost:8000/api/v1/knowledge/search?query=SSL&top_k=5"
```

### 🧪 测试

#### 运行全部测试

```bash
cd backend
pytest tests/ -v
```

#### 测试覆盖

| 测试类型   | 路径                           | 说明                      |
| ---------- | ------------------------------ | ------------------------- |
| Agent 测试 | `tests/test_agents/`           | Supervisor Agent 意图路由 |
| API 测试   | `tests/test_api/`              | 聊天、知识库 API          |
| 数据库测试 | `tests/test_db/`               | 数据模型、会话            |
| 服务测试   | `tests/test_services/`         | LLM 路由、知识库服务      |
| 配置测试   | `tests/test_config.py`         | 环境变量配置              |
| Mock 测试  | `tests/test_mock_providers.py` | Mock 提供者               |

#### 测试覆盖率

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### 🔧 开发规范

#### TDD 流程

本项目遵循 **TDD（测试驱动开发）** 流程：

```
1. RED: 编写测试 → 运行确认失败
2. GREEN: 编写最简实现 → 运行测试通过
3. REFACTOR: 优化代码 → 测试仍通过
```

#### 代码提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>
```

**Type 列表**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

**示例**:

```
feat(chat): 实现 SSE 流式响应

- 实现基于 LangGraph 的 Supervisor Agent
- 支持知识检索和意图路由
- 添加会话管理 API

Closes #12
```

#### Git 钩子

- **pre-commit**: 自动运行 `ruff check` + `ruff format`
- **commit-msg**: 校验提交信息格式

### 📦 Docker 部署

#### 使用 Docker Compose

```bash
# 启动所有服务 (PostgreSQL + Backend + Frontend)
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
```

#### 服务列表

| 服务        | 端口 | 说明                         |
| ----------- | ---- | ---------------------------- |
| PostgreSQL  | 5432 | 主数据库（带 pgvector 扩展） |
| Backend API | 8000 | FastAPI 后端服务             |
| Frontend    | 3000 | React 前端（开发模式）       |

#### 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# LLM API Key (必填)
LLM_API_KEY=your-openai-api-key

# 可选配置
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

### ⚙️ 环境变量

| 变量                   | 说明         | 默认值                                                             |
| ---------------------- | ------------ | ------------------------------------------------------------------ |
| `APP_NAME`             | 应用名称     | Tech Support Assistant                                             |
| `DEBUG`                | 调试模式     | false                                                              |
| `DB_DSN`               | 数据库连接   | postgresql+asyncpg://postgres:postgres@localhost:5432/tech_support |
| `LLM_PROVIDER`         | LLM 提供者   | openai                                                             |
| `LLM_API_KEY`          | LLM API Key  | (必填)                                                             |
| `LLM_BASE_URL`         | LLM API 地址 | https://api.openai.com/v1                                          |
| `LLM_MODEL`            | LLM 模型     | gpt-4o-mini                                                        |
| `EMBEDDING_PROVIDER`   | 嵌入提供者   | openai                                                             |
| `EMBEDDING_MODEL`      | 嵌入模型     | text-embedding-3-small                                             |
| `EMBEDDING_DIMENSIONS` | 嵌入维度     | 1536                                                               |

### 📄 相关文档

| 文档                   | 说明                 |
| ---------------------- | -------------------- |
| [PRD.md](PRD.md)       | 产品需求文档         |
| [design.md](design.md) | 架构设计文档         |
| [plan.md](plan.md)     | 实现计划             |
| [SPEC.md](SPEC.md)     | 技术规范文档         |
| [AGENTS.md](AGENTS.md) | Agent 架构和测试说明 |

### 📝 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

## English

### 📖 Introduction

**Tech Support Assistant** is an enterprise AI Agent platform designed for internal technical support teams. It leverages AI automation to help support engineers resolve customer issues more efficiently.

### ✨ Key Features

| Feature                                | Description                                                         |
| -------------------------------------- | ------------------------------------------------------------------- |
| 🔍 **Intelligent Knowledge Retrieval** | RAG-based Q&A with vector search, cosine similarity and citations   |
| 📝 **Text Chunking**                   | Intelligent chunking with paragraph-level splitting and overlap     |
| 🩺 **AI-Powered Diagnosis**            | AI-driven fault diagnosis with pattern matching and LLM suggestions |
| 📋 **Ticket Management**               | Create, query, update tickets with priority and status management   |
| 🤖 **Multi-Agent Collaboration**       | Supervisor Agent routes intent to knowledge or diagnosis agents     |
| 💬 **SSE Streaming Chat**              | Real-time streaming responses with citation source display          |
| 📚 **Knowledge Base Management**       | Document upload, chunking, vectorization with full CRUD             |
| 🖥️ **React Frontend**                  | Complete chat/diagnosis/knowledge base interface                    |
| 🏥 **Health Check**                    | API health monitoring for quick service diagnostics                 |
| 🧪 **TDD-Driven**                      | Complete test suite covering Agents, APIs, DB, Services             |

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
│   │   │   └── diagnosis.py             #   Diagnosis Agent
│   │   ├── api/                          # API routes
│   │   │   └── v1/
│   │   │       ├── chat.py              #   Chat API
│   │   │       ├── health.py           #   Health check
│   │   │       ├── knowledge.py        #   Knowledge API
│   │   │       └── diagnosis.py         #   Diagnosis API
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
│   │   │   └── ticket.py               #   Ticket model
│   │   ├── services/                     # Business services
│   │   │   ├── knowledge.py            #   Knowledge service
│   │   │   ├── llm.py                  #   LLM router
│   │   │   ├── chunking.py             #   Text chunking
│   │   │   ├── rag.py                  #   RAG retrieval
│   │   │   ├── diagnosis.py            #   Error diagnosis
│   │   │   └── ticket.py               #   Ticket service
│   │   ├── main.py                       #   Application entry
│   │   └── ...
│   ├── tests/                            # Test suite
│   │   ├── conftest.py                  #   Global fixtures
│   │   ├── mock_providers.py            #   Mock providers
│   │   ├── test_agents/                 #   Agent tests
│   │   │   └── test_diagnosis.py       #     Diagnosis agent tests
│   │   ├── test_api/                    #   API tests
│   │   │   └── test_diagnosis.py       #     Diagnosis API tests
│   │   ├── test_db/                     #   Database tests
│   │   │   ├── test_error_pattern.py   #     Error pattern tests
│   │   │   └── test_ticket.py          #     Ticket model tests
│   │   └── test_services/              #   Service tests
│   │       ├── test_diagnosis.py       #     Diagnosis service tests
│   │       └── test_ticket.py          #     Ticket service tests
│   ├── alembic/                          # Database migrations
│   └── pyproject.toml                   # Project config
├── frontend/                             # Frontend Application
│   ├── src/
│   │   ├── pages/                        #   Page components
│   │   │   ├── ChatPage.tsx            #     Chat page
│   │   │   ├── DiagnosisPage.tsx       #     Fault diagnosis page
│   │   │   └── KnowledgeBasePage.tsx  #     Knowledge base management
│   │   ├── services/                     #   API services
│   │   │   ├── knowledge.ts            #     Knowledge API
│   │   │   └── diagnosis.ts            #     Diagnosis API
│   │   ├── store/                        #   Redux Store
│   │   │   ├── index.ts               #     Store config
│   │   │   └── conversationSlice.ts   #     Conversation state
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

| Method             | Path                                       | Description                  |
| ------------------ | ------------------------------------------ | ---------------------------- |
| **Health**         |                                            |                              |
| GET                | `/api/v1/health`                           | Service health check         |
| **Conversations**  |                                            |                              |
| GET                | `/api/v1/chat/conversations`               | List conversations           |
| POST               | `/api/v1/chat/conversations`               | Create new conversation      |
| GET                | `/api/v1/chat/conversations/{id}`          | Get conversation details     |
| DELETE             | `/api/v1/chat/conversations/{id}`          | Delete conversation          |
| GET                | `/api/v1/chat/conversations/{id}/messages` | Get conversation messages    |
| **Chat**           |                                            |                              |
| POST               | `/api/v1/chat/completions`                 | Send message (SSE streaming) |
| **Knowledge Base** |                                            |                              |
| POST               | `/api/v1/knowledge/documents`              | Upload document              |
| GET                | `/api/v1/knowledge/documents`              | List documents               |
| GET                | `/api/v1/knowledge/documents/{id}`         | Get document details         |
| DELETE             | `/api/v1/knowledge/documents/{id}`         | Delete document              |
| POST               | `/api/v1/knowledge/search`                 | Search knowledge base        |

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

### 🧪 Testing

#### Run All Tests

```bash
cd backend
pytest tests/ -v
```

#### Test Categories

| Type           | Path                           | Description                      |
| -------------- | ------------------------------ | -------------------------------- |
| Agent Tests    | `tests/test_agents/`           | Supervisor Agent intent routing  |
| API Tests      | `tests/test_api/`              | Chat and Knowledge APIs          |
| Database Tests | `tests/test_db/`               | Data models and sessions         |
| Service Tests  | `tests/test_services/`         | LLM router and knowledge service |
| Config Tests   | `tests/test_config.py`         | Environment configuration        |
| Mock Tests     | `tests/test_mock_providers.py` | Mock providers                   |

#### Test Coverage

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### 🔧 Development Guidelines

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

### 📦 Docker Deployment

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
```

### ⚙️ Environment Variables

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

### 📄 Related Documentation

| Document               | Description                    |
| ---------------------- | ------------------------------ |
| [PRD.md](PRD.md)       | Product Requirements Document  |
| [design.md](design.md) | Architecture Design Document   |
| [plan.md](plan.md)     | Implementation Plan            |
| [SPEC.md](SPEC.md)     | Technical Specification        |
| [AGENTS.md](AGENTS.md) | Agent architecture and testing |

### 📝 License

This project is licensed under the [MIT License](LICENSE).
