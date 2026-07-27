# 技术支持助手 - 技术规范文档 (SPEC)

> 版本: 0.1.0  
> 最后更新: 2026-07-27

---

## 1. 技术栈规范

### 1.1 后端技术栈

| 类别        | 技术              | 版本要求 | 用途                |
| ----------- | ----------------- | -------- | ------------------- |
| 语言        | Python            | >= 3.12  | 主开发语言          |
| Web 框架    | FastAPI           | >= 0.115 | REST API + SSE      |
| ASGI 服务器 | Uvicorn           | >= 0.30  | 生产服务器          |
| ORM         | SQLAlchemy        | >= 2.0   | 数据库访问          |
| 数据库      | PostgreSQL        | >= 16    | 主数据库            |
| 向量扩展    | pgvector          | >= 0.3   | 向量检索            |
| 异步驱动    | asyncpg           | >= 0.30  | PostgreSQL 异步驱动 |
| 数据库迁移  | Alembic           | >= 1.13  | 数据库版本管理      |
| 数据验证    | Pydantic          | >= 2.0   | Schema 验证         |
| Agent 框架  | LangGraph         | >= 0.2   | AI Agent 编排       |
| LLM SDK     | OpenAI Python     | >= 1.50  | LLM API 调用        |
| 配置管理    | pydantic-settings | >= 2.0   | 环境变量管理        |

### 1.2 前端技术栈 (规划中)

| 类别        | 技术          | 版本要求 | 用途       |
| ----------- | ------------- | -------- | ---------- |
| 语言        | TypeScript    | >= 5.0   | 主开发语言 |
| 框架        | React         | >= 18    | UI 框架    |
| 构建工具    | Vite          | >= 5.0   | 开发/构建  |
| 状态管理    | Redux Toolkit | >= 2.0   | 全局状态   |
| UI 组件     | Ant Design    | >= 5.0   | UI 组件库  |
| 路由        | React Router  | >= 6.0   | 路由管理   |
| HTTP 客户端 | Axios         | >= 1.6   | API 请求   |

### 1.3 开发工具

| 工具             | 版本要求   | 用途       |
| ---------------- | ---------- | ---------- |
| Git              | >= 2.40    | 版本控制   |
| Docker           | >= 24      | 容器化部署 |
| Docker Compose   | >= 2       | 多服务编排 |
| VS Code          | 最新       | 推荐 IDE   |
| Python 包管理器  | pip / uv   | 依赖管理   |
| Node.js 包管理器 | npm / pnpm | 依赖管理   |

---

## 2. 项目结构规范

### 2.1 后端目录结构

```
backend/
├── app/
│   ├── __init__.py           # 应用入口标记
│   ├── main.py               # FastAPI 应用入口
│   ├── api/                  # API 路由层
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── chat.py       # 聊天相关 API
│   │       ├── health.py     # 健康检查 API
│   │       └── knowledge.py  # 知识库 API
│   ├── core/                 # 核心配置
│   │   ├── __init__.py
│   │   └── config.py         # 全局配置
│   ├── db/                   # 数据库层
│   │   ├── __init__.py
│   │   ├── base.py           # 基础模型类
│   │   ├── guid.py           # UUID 生成
│   │   └── session.py        # 数据库会话管理
│   ├── models/               # 数据模型
│   │   ├── __init__.py
│   │   ├── conversation.py   # 会话模型
│   │   └── knowledge.py      # 知识库模型
│   ├── schemas/              # Pydantic Schema
│   │   └── __init__.py
│   ├── services/             # 业务服务层
│   │   ├── __init__.py
│   │   ├── knowledge.py      # 知识库服务
│   │   └── llm.py            # LLM 路由服务
│   ├── agents/               # AI Agent 定义
│   │   ├── __init__.py
│   │   └── supervisor.py     # Supervisor Agent
│   └── tools/                # Agent 工具
│       └── __init__.py
├── tests/                    # 测试目录
│   ├── __init__.py
│   ├── conftest.py           # 全局测试 fixtures
│   ├── mock_providers.py     # Mock 提供者
│   ├── test_config.py        # 配置测试
│   ├── test_agents/          # Agent 测试
│   ├── test_api/             # API 测试
│   ├── test_db/              # 数据库测试
│   └── test_services/        # 服务测试
├── alembic/                  # 数据库迁移
│   ├── README
│   ├── env.py
│   └── script.py.mako
├── alembic.ini               # Alembic 配置
├── pyproject.toml            # 项目配置
└── Dockerfile                # Docker 构建文件
```

### 2.2 前端目录结构 (规划中)

```
frontend/
├── src/
│   ├── __tests__/            # 测试文件
│   │   └── conversationSlice.test.ts
│   ├── components/           # 通用组件
│   ├── pages/                # 页面组件
│   │   └── ChatPage.tsx      # 聊天页面
│   ├── store/                # Redux Store
│   │   ├── index.ts
│   │   └── conversationSlice.ts
│   ├── services/             # API 服务
│   ├── types/                # TypeScript 类型定义
│   ├── App.tsx               # 根组件
│   └── main.tsx              # 入口文件
├── public/                   # 静态资源
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

### 2.3 根目录结构

```
technical-support-assistant/
├── backend/                  # 后端应用
├── frontend/                 # 前端应用 (规划中)
├── docker-compose.yml        # Docker 编排
├── .env.example              # 环境变量示例
├── .gitignore                # Git 忽略规则
├── PRD.md                    # 产品需求文档
├── design.md                 # 架构设计文档
├── plan.md                   # 实现计划
├── SPEC.md                   # 技术规范文档
├── README.md                 # 项目说明
└── LICENSE                   # 许可证
```

---

## 3. 代码规范

### 3.1 Python 代码规范

- **PEP 8**: 遵循 Python 风格指南
- **格式化工具**: Ruff (替代 black + isort)
- **类型注解**: 所有函数必须有类型注解
- **文档字符串**: 使用 Google 风格 docstring
- **行宽**: 120 字符
- **命名约定**:
  - 模块: snake_case
  - 类: PascalCase
  - 函数/方法: snake_case
  - 变量: snake_case
  - 常量: UPPER_SNAKE_CASE

### 3.2 TypeScript 代码规范

- **ESLint**: 使用 @typescript-eslint
- **Prettier**: 代码格式化
- **严格模式**: 启用 strict mode
- **命名约定**:
  - 文件: kebab-case
  - 组件: PascalCase
  - 变量/函数: camelCase
  - 常量: UPPER_SNAKE_CASE
  - 接口/类型: PascalCase (I 前缀可选)

### 3.3 Git 提交规范

**Conventional Commits 格式**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 列表**:

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `build`: 构建系统
- `ci`: CI/CD 配置
- `chore`: 其他变更

**示例**:

```
feat(chat): 实现 SSE 流式响应

- 实现基于 LangGraph 的 Supervisor Agent
- 支持知识检索和意图路由
- 添加会话管理 API

Closes #12
```

---

## 4. API 规范

### 4.1 API 版本化

所有 API 路径必须包含版本前缀: `/api/v1/`

### 4.2 RESTful 设计

| 方法   | 用途              | 示例                                    |
| ------ | ----------------- | --------------------------------------- |
| GET    | 获取资源列表/详情 | `GET /api/v1/chat/conversations`        |
| POST   | 创建资源          | `POST /api/v1/chat/conversations`       |
| PUT    | 更新完整资源      | `PUT /api/v1/chat/conversations/:id`    |
| PATCH  | 部分更新资源      | `PATCH /api/v1/chat/conversations/:id`  |
| DELETE | 删除资源          | `DELETE /api/v1/chat/conversations/:id` |

### 4.3 响应格式

**成功响应**:

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-07-27T12:00:00Z"
  }
}
```

**错误响应**:

```json
{
  "error": {
    "code": "CONVERSATION_NOT_FOUND",
    "message": "会话不存在",
    "details": null
  }
}
```

### 4.4 状态码规范

| 状态码 | 说明               |
| ------ | ------------------ |
| 200    | 请求成功           |
| 201    | 资源创建成功       |
| 204    | 删除成功（无返回） |
| 400    | 请求参数错误       |
| 401    | 未认证             |
| 403    | 无权限             |
| 404    | 资源不存在         |
| 422    | 数据验证失败       |
| 500    | 服务器内部错误     |

---

## 5. 数据库规范

### 5.1 命名规范

- 表名: snake_case, 复数形式 (如 `knowledge_documents`)
- 列名: snake_case
- 索引: `idx_[表名]_[列名]`
- 外键: `fk_[表名]_[列名]`

### 5.2 基础字段

每个表必须包含:

- `id`: UUID 主键
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 5.3 数据类型

- 主键: UUID
- 文本: VARCHAR(指定长度) / TEXT
- JSON: JSONB (PostgreSQL)
- 时间: TIMESTAMPTZ
- 向量: VECTOR(pgvector)

---

## 6. 测试规范

### 6.1 测试类型

| 类型       | 框架                     | 覆盖率目标    | 说明           |
| ---------- | ------------------------ | ------------- | -------------- |
| 单元测试   | pytest + pytest-asyncio  | >= 90%        | 函数/类级别    |
| 集成测试   | httpx.AsyncClient        | >= 80%        | API 端点级别   |
| Agent 测试 | LangGraph tester         | 100% 核心路径 | Graph 状态转换 |
| 前端测试   | Vitest + Testing Library | >= 70%        | 组件级别       |

### 6.2 TDD 流程

```
1. RED: 编写测试 → 运行确认失败
2. GREEN: 编写最简实现 → 运行测试通过
3. REFACTOR: 优化代码 → 测试仍通过
```

**铁律**:

- 先写测试，后写实现
- 测试不通过不可提交代码
- 所有外部依赖使用 Mock

### 6.3 测试文件组织

```
tests/
├── conftest.py          # 全局 fixtures
├── mock_providers.py    # Mock 提供者
├── test_config.py       # 配置测试
├── test_agents/         # Agent 测试
├── test_api/            # API 集成测试
├── test_db/             # 数据库测试
└── test_services/       # 服务层测试
```

---

## 7. 安全规范

### 7.1 环境变量

- 所有密钥通过 `.env` 文件注入
- `.env` 文件必须加入 `.gitignore`
- 提供 `.env.example` 作为模板

### 7.2 认证授权 (规划中)

- OAuth2/OIDC 认证
- RBAC 权限控制
- API Key 管理

### 7.3 数据安全

- 全链路 TLS 加密
- SQL 注入防护 (ORM 参数化查询)
- XSS 防护 (前端框架自动转义)
- 敏感信息日志脱敏

---

## 8. 部署规范

### 8.1 环境要求

| 组件       | 最低版本 |
| ---------- | -------- |
| Python     | 3.12     |
| PostgreSQL | 16       |
| pgvector   | 0.5      |
| Node.js    | 20       |
| Docker     | 24       |

### 8.2 Docker Compose

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    # ... 配置

  backend:
    build: ./backend
    # ... 配置

  frontend:
    build: ./frontend
    # ... 配置
```

### 8.3 常用命令

```bash
# 开发
cd backend && pip install -e ".[dev]"
cd backend && uvicorn app.main:app --reload

# 测试
cd backend && pytest tests/ -v

# 数据库迁移
cd backend && alembic upgrade head
```

---

## 9. 依赖管理

### 9.1 后端依赖

依赖定义在 `backend/pyproject.toml` 中。

**核心依赖**:

- fastapi, uvicorn, sqlalchemy, asyncpg
- alembic, pgvector, pydantic
- langgraph, langchain, openai

**开发依赖**:

- pytest, pytest-asyncio, pytest-cov
- httpx, ruff, factory-boy

### 9.2 前端依赖 (规划中)

依赖定义在 `frontend/package.json` 中。

**核心依赖**:

- react, react-dom, redux-toolkit, antd
- react-router-dom, axios

**开发依赖**:

- vitest, @testing-library/react, eslint

---

## 10. 代码质量

### 10.1 静态分析

```bash
# Python
ruff check backend/app/
ruff format --check backend/app/

# TypeScript (规划中)
npx tsc --noEmit
npx eslint src/
```

### 10.2 测试覆盖

```bash
cd backend && pytest tests/ --cov=app --cov-report=term-missing
```

### 10.3 CI/CD (规划中)

- GitHub Actions 自动运行测试
- 代码覆盖率报告
- 自动构建 Docker 镜像
