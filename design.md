# 技术支持助手 - 企业级 Agent 架构设计

## 1. 项目概述

构建面向内部技术支持团队的企业级 AI Agent 平台，以 Web 聊天界面提供综合型技术支持能力。系统采用 **LangGraph 多智能体架构**，支持知识问答、故障诊断、工单管理，具备企业级的安全性、可观测性和可扩展性。

## 2. 企业级架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         客户端层                                      │
│  Web UI (React)  │  IM 集成 (飞书/钉钉/Slack)  │  API 对接           │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                       网关层                                         │
│  Nginx/ALB │ Auth (OAuth2/OIDC) │ Rate Limiting │ Audit Logging    │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                      FastAPI 服务层                                  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   LangGraph Agent Orchestrator                 │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │ │
│  │  │Supervisor│ │Knowledge │ │Diagnosis │ │   Escalation     │ │ │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │     Agent        │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────────────┐ │ │
│  │  │  Ticket  │ │  Data    │ │   Tool Executor (sandbox)    │ │ │
│  │  │  Agent   │ │  Agent   │ │                               │ │ │
│  │  └──────────┘ └──────────┘ └──────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐    │
│  │LLM Router│ │Embedding │ │  Tool    │ │   Memory System    │    │
│  │OpenAI    │ │  Service │ │ Registry │ │ Conv │ Entity │ DB │    │
│  │Ollama    │ │          │ │          │ │                    │    │
│  │LiteLLM   │ │          │ │          │ │                    │    │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                       数据层                                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐  │
│  │ PostgreSQL │ │  pgvector  │ │   Redis    │ │  Object Store  │  │
│  │  (业务数据) │ │  (向量)    │ │ (缓存/队列) │ │  (文档附件)    │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                    可观测性层                                         │
│  LangSmith / OpenTelemetry / Prometheus / Grafana / ELK             │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Agent 框架选型：LangGraph

### 为什么选择 LangGraph

| 维度     | LangGraph          | LangChain Agent | CrewAI    | AutoGen |
| -------- | ------------------ | --------------- | --------- | ------- |
| 图编排   | 原生 DAG/循环图    | 线性链          | 顺序/层级 | 对话图  |
| 状态管理 | 内置 StateGraph    | 手动            | 有限      | 有限    |
| 人机协同 | 原生支持 interrupt | 不支持          | 不支持    | 支持    |
| 条件路由 | 原生支持           | 需 hack         | 有限      | 有限    |
| 生产化   | LangSmith 深度集成 | 基础            | 较新      | 较新    |

### 核心概念映射

```
Graph (图) → Agent 工作流
Node (节点) → 每个 Agent / 工具调用 / 决策点
Edge (边) → 条件路由 / 顺序执行
State (状态) → 跨 Agent 共享的对话上下文
Interrupt → 人工介入检查点
```

## 4. 多 Agent 体系设计

### 4.1 Supervisor Agent (路由仲裁者)

**职责**：入口 Agent，分析用户意图，路由到对应子 Agent

```
用户问题
    │
Supervisor Agent
    │
    ├─ 知识问答类 ──────────► Knowledge Agent
    ├─ 故障排查类 ──────────► Diagnosis Agent
    ├─ 工单相关 ───────────► Ticket Agent
    ├─ 数据查询类 ──────────► Data Agent
    ├─ 需要升级二线 ───────► Escalation Agent
    └─ 多步复杂问题 ───────► 协调多个子 Agent 协作
```

**State 定义**：

```python
class AgentState(TypedDict):
    messages: list              # 对话历史
    user_intent: str            # 用户意图分类
    sub_agent_outputs: dict     # 子 Agent 输出汇总
    knowledge_context: list     # 检索到的知识片段
    diagnosis_result: dict      # 诊断结果
    ticket_info: dict           # 工单信息
    escalation_needed: bool     # 是否需要升级
    human_approval: bool        # 人工确认状态
    error_info: str             # 错误信息
```

### 4.2 Knowledge Agent (知识问答 Agent)

**能力**：

- RAG 检索增强生成
- 多文档源混合检索
- 引用溯源与置信度评分
- 追问澄清

**工具集**：

- `search_knowledge_base(query, filters)` → 向量搜索知识库
- `hybrid_search(query, keywords)` → 向量+关键词混合搜索
- `get_document_detail(doc_id)` → 获取文档详情
- `ask_clarification(question)` → 向用户追问

**Graph 流程**：

```
[用户问题] → [意图识别] → [知识检索] → [LLM 生成回答] → [引用标注] → [输出]
                                      ↕
                               [置信度 < 阈值?] ──► [追问澄清]
```

### 4.3 Diagnosis Agent (故障诊断 Agent)

**能力**：

- 基于症状分析根因
- 生成结构化排查流程
- 逐步引导用户操作
- 收集诊断结果反馈

**工具集**：

- `analyze_symptoms(symptoms)` → 症状分析
- `get_diagnosis_flow(scenario)` → 获取诊断流程
- `run_health_check(service)` → 运行健康检查
- `collect_logs(source, time_range)` → 收集日志
- `generate_report(diagnosis_data)` → 生成诊断报告

**Graph 流程**：

```
[症状输入] → [症状分析 Agent] → [假设生成]
    │                              │
    │                         [排查步骤执行] ←── [人工确认]
    │                              │
    │                         [结果验证]
    │                              │
    └──── [根因确定] ←── [否，继续排查]
                │
          [生成诊断报告] → [建议解决方案]
                │
          [是否需要升级?] ──► Escalation Agent
```

### 4.4 Ticket Agent (工单管理 Agent)

**能力**：

- 从对话自动提取工单信息
- 创建/更新/查询工单
- 关联历史相似工单

**工具集**：

- `create_ticket(summary, description, priority, customer_info)` → 创建工单
- `update_ticket(ticket_id, status, resolution)` → 更新工单
- `search_tickets(query, filters)` → 搜索工单
- `get_ticket_detail(ticket_id)` → 获取工单详情
- `find_similar_tickets(description)` → 查找相似历史工单

### 4.5 Escalation Agent (升级/转交 Agent)

**能力**：

- 判断何时需要升级到二线
- 生成升级摘要（包含完整的排查上下文）
- 选择匹配的二线工程师/团队
- 跟踪升级状态

**工具集**：

- `generate_escalation_summary(context)` → 生成升级摘要
- `find_available_engineers(team, expertise)` → 查找可用工程师
- `escalate_ticket(ticket_id, assignee, summary)` → 升级工单
- `notify_escalation(channel, message)` → 通知相关人员

### 4.6 Data Agent (数据查询 Agent)

**能力**：

- 查询客户信息、产品信息、订单状态等业务数据
- 在授权范围内执行数据库查询
- 数据可视化建议

**工具集**：

- `query_customer_info(customer_id)` → 查询客户信息
- `query_order_status(order_id)` → 查询订单状态
- `query_product_info(product_id)` → 查询产品信息
- `run_sql_query(sql_template, params)` → 执行预定义 SQL
- `check_permission(resource, action)` → 权限检查

## 5. 企业级基础设施

### 5.1 认证与授权

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  身份提供商   │     │  Auth 网关   │     │   Agent 平台  │
│  (OIDC/OAuth2)│     │   (验证JWT)  │     │   (RBAC 鉴权) │
│              │────►│              │────►│              │
│  Azure AD /  │     │  验证 token  │     │  角色权限检查 │
│  Keycloak    │     │  注入身份信息 │     │  数据权限过滤 │
└──────────────┘     └──────────────┘     └──────────────┘
```

**RBAC 角色模型**：

| 角色        | 权限                               |
| ----------- | ---------------------------------- |
| admin       | 全部权限，含 LLM 配置、用户管理    |
| engineer_l2 | 知识库管理、诊断流程编辑、工单管理 |
| engineer_l1 | 聊天对话、知识检索、创建工单       |
| viewer      | 只读访问知识库和对话历史           |

### 5.2 多租户

- **数据隔离**：按 tenant_id 行级隔离（RLS）
- **知识库隔离**：每个租户独立知识库 namespace
- **LLM 配置隔离**：租户级模型/API Key 配置
- **用量统计**：租户级 token 消耗计量

### 5.3 可观测性

```
┌────────────────────────────────────────────────┐
│               OpenTelemetry                     │
│                                                  │
│  LLM Traces (LangSmith)                          │
│  │  ├─ Token 消耗                                │
│  │  ├─ Latency 分析                              │
│  │  └─ 回答质量评分                              │
│                                                  │
│  Application Metrics (Prometheus)                 │
│  │  ├─ API QPS / Latency P50/P95/P99             │
│  │  ├─ Agent 调用次数/成功率                     │
│  │  └─ 工具调用成功率                            │
│                                                  │
│  Logs (ELK / Loki)                               │
│  │  ├─ 全量审计日志                              │
│  │  ├─ Agent 决策路径                            │
│  │  └─ 异常/错误追踪                             │
│                                                  │
│  Alerts (Grafana Alertmanager)                    │
│     ├─ LLM 错误率 > 5%                          │
│     ├─ P95 Latency > 10s                        │
│     └─ Agent 循环/卡死检测                       │
└──────────────────────────────────────────────────┘
```

### 5.4 审计日志

每条 Agent 操作记录：

```json
{
  "event_id": "uuid",
  "timestamp": "2026-07-22T12:00:00Z",
  "tenant_id": "tenant_001",
  "user_id": "user_123",
  "session_id": "conv_456",
  "event_type": "agent_action",
  "agent_name": "KnowledgeAgent",
  "action": "search_knowledge_base",
  "input": { "query": "如何配置SSL证书" },
  "output_summary": "返回3条相关文档",
  "llm_tokens": 1250,
  "latency_ms": 2340,
  "status": "success"
}
```

## 6. 工具系统 (Tool System)

### 6.1 工具注册与发现

```python
# 工具注册模式
@tool_registry.register(
    name="search_knowledge_base",
    description="搜索知识库获取相关信息",
    category="knowledge",
    timeout=30,
    requires_permission=["knowledge:read"],
    rate_limit="100/minute"
)
async def search_knowledge_base(query: str, filters: dict = None) -> list[Document]:
    ...
```

### 6.2 工具分类

| 类别       | 工具                                               | 所属 Agent |
| ---------- | -------------------------------------------------- | ---------- |
| knowledge  | search_knowledge_base, hybrid_search, get_document | Knowledge  |
| diagnosis  | analyze_symptoms, run_health_check, collect_logs   | Diagnosis  |
| ticket     | create_ticket, update_ticket, search_tickets       | Ticket     |
| escalation | generate_summary, find_engineers, escalate         | Escalation |
| data       | query_customer, query_order, run_sql               | Data       |
| system     | check_permission, get_system_status                | Common     |

## 7. 内存系统 (Memory)

### 7.1 三层内存架构

```
┌─────────────────────────────────────────────┐
│               Agent 内存系统                  │
│                                              │
│  Short-term (对话窗口)                       │
│  ├─ 当前对话消息列表                         │
│  ├─ Token 窗口管理 (滑动窗口)                │
│  └─ Redis 缓存 (TTL: 24h)                    │
│                                              │
│  Long-term (持久化存储)                      │
│  ├─ 完整对话历史 (PostgreSQL)                 │
│  ├─ 关键信息摘要提取                         │
│  └─ 用户偏好/习惯学习                       │
│                                              │
│  Entity (业务实体记忆)                       │
│  ├─ 客户信息缓存                             │
│  ├─ 产品/系统配置上下文                       │
│  └─ 历史工单关联                             │
└──────────────────────────────────────────────┘
```

## 8. LLM 与企业级模型管理

### 8.1 模型路由策略

```python
# 按场景智能路由
ROUTING_STRATEGY = {
    "simple_qa": {          # 简单问答
        "model": "gpt-4o-mini",
        "max_tokens": 1024,
        "temperature": 0.3
    },
    "diagnosis": {          # 故障诊断
        "model": "gpt-4o",
        "max_tokens": 4096,
        "temperature": 0.2,
        "tools": ["analyze", "health_check"]
    },
    "ticket_generation": {  # 工单生成
        "model": "gpt-4o-mini",
        "max_tokens": 2048,
        "temperature": 0.5
    },
    "complex_reasoning": {  # 复杂推理
        "model": "gpt-4o",
        "max_tokens": 8192,
        "temperature": 0.1
    }
}
```

### 8.2 企业级 LLM 保障

- **Fallback 链**：主模型失败 → 备用模型 → 降级回复
- **断路器**：连续 N 次失败后熔断，自动切换
- **重试策略**：指数退避 + 抖动
- **Token 预算**：每个 Agent/场景设置 token 上限
- **成本追踪**：按租户/用户/场景统计模型调用成本

## 9. 与工单系统集成

### 9.1 架构

```
Agent 平台 ──► 工单适配层 ──► Webhook / API
                    │
           ┌────────┼────────┐
           ▼        ▼        ▼
         Jira    Zendesk  ServiceNow
```

### 9.2 集成流程

1. 一线排查后无法解决 → Escalation Agent 介入
2. 自动汇总对话上下文、排查步骤、日志快照
3. 生成结构化工单（优先级、分类、描述）
4. 创建外部工单，返回工单号
5. 后续可查询工单状态更新

## 10. 数据模型

### 10.1 核心业务表

```sql
-- 租户
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    config JSONB,        -- LLM配置、功能开关等
    created_at TIMESTAMP
);

-- 用户
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255),
    role VARCHAR(50),     -- admin / engineer_l2 / engineer_l1 / viewer
    external_id VARCHAR(255),  -- SSO ID
    metadata JSONB,
    created_at TIMESTAMP
);

-- Agent 会话
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    agent_graph TEXT,     -- LangGraph 实例快照
    metadata JSONB,
    status VARCHAR(50),   -- active / resolved / escalated
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 消息
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES agent_conversations(id),
    role VARCHAR(50),      -- user / assistant / system / tool
    content TEXT,
    agent_name VARCHAR(100), -- 产生消息的 Agent
    tool_calls JSONB,
    sources JSONB,          -- 知识来源引用
    tokens_used INT,
    latency_ms INT,
    metadata JSONB,
    created_at TIMESTAMP
);

-- 知识文档
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    title VARCHAR(500),
    content TEXT,
    doc_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 文档向量片段
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    content TEXT,
    embedding VECTOR(1536),
    chunk_index INT,
    metadata JSONB
);

-- 工单关联
CREATE TABLE ticket_links (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES agent_conversations(id),
    external_system VARCHAR(50),  -- jira / zendesk / servicenow
    external_ticket_id VARCHAR(255),
    ticket_summary TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 审计日志
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(100),
    agent_name VARCHAR(100),
    action VARCHAR(100),
    input JSONB,
    output_summary TEXT,
    tokens_used INT,
    latency_ms INT,
    status VARCHAR(50),
    ip_address INET,
    created_at TIMESTAMP
);
```

### 10.2 索引策略

```sql
-- 向量索引
CREATE INDEX idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 搜索索引
CREATE INDEX idx_knowledge_metadata ON knowledge_documents USING GIN (metadata);
CREATE INDEX idx_messages_created ON agent_messages (conversation_id, created_at);

-- 审计索引
CREATE INDEX idx_audit_tenant_time ON audit_logs (tenant_id, created_at DESC);
CREATE INDEX idx_audit_user ON audit_logs (user_id, created_at DESC);
```

## 11. API 设计

### 11.1 Chat API (SSE 流式)

```
POST   /api/v1/chat/completions      # 发送消息，流式返回
GET    /api/v1/chat/conversations     # 会话列表
POST   /api/v1/chat/conversations     # 创建会话
GET    /api/v1/chat/conversations/:id # 会话详情
DELETE /api/v1/chat/conversations/:id # 删除会话
GET    /api/v1/chat/conversations/:id/messages  # 消息历史
```

### 11.2 Agent 管理

```
POST   /api/v1/agents/:name/invoke   # 直接调用特定 Agent
GET    /api/v1/agents/stats          # Agent 调用统计
```

### 11.3 知识库 API

```
POST   /api/v1/knowledge/documents      # 上传文档
GET    /api/v1/knowledge/documents      # 文档列表
GET    /api/v1/knowledge/documents/:id  # 文档详情
DELETE /api/v1/knowledge/documents/:id  # 删除文档
POST   /api/v1/knowledge/search        # 搜索知识库
POST   /api/v1/knowledge/reindex       # 重建索引
```

### 11.4 诊断 API

```
POST   /api/v1/diagnosis/analyze      # 分析故障
POST   /api/v1/diagnosis/flow/:id     # 执行诊断流程
POST   /api/v1/diagnosis/feedback     # 诊断反馈
```

### 11.5 工单 API

```
POST   /api/v1/tickets/create         # 创建工单
GET    /api/v1/tickets/:id            # 查询工单
POST   /api/v1/tickets/:id/update     # 更新工单
```

### 11.6 管理 API

```
GET    /api/v1/admin/stats            # 平台统计
GET    /api/v1/admin/audit-logs       # 审计日志
POST   /api/v1/admin/llm-config       # LLM 配置
GET    /api/v1/admin/usage-report     # 用量报告
```

## 12. 前端设计

### 12.1 技术选型

- **框架**：React 18 + TypeScript
- **状态管理**：Redux Toolkit
- **UI 组件**：Ant Design 5.x
- **流式渲染**：Server-Sent Events + React Streaming
- **路由**：React Router v6

### 12.2 页面结构

```
/chat                  # 聊天主界面
/chat/:id              # 特定会话
/knowledge             # 知识库管理
/knowledge/:id         # 文档详情
/diagnosis             # 诊断流程管理
/diagnosis/flows       # 诊断流程列表
/tickets               # 工单列表
/admin/dashboard       # 管理看板
/admin/llm-config      # LLM 配置
/admin/audit-logs      # 审计日志
/admin/users           # 用户管理
```

### 12.3 聊天界面组件

```
┌──────────────────────────────────────────┐
│  Sidebar           │  Chat Area          │
│  ┌──────┐          │  ┌──────────────┐  │
│  │ 搜索  │          │  │ Agent 状态条  │  │
│  ├──────┤          │  │ (当前使用的   │  │
│  │对话1  │          │  │  Agent)      │  │
│  │对话2  │          │  ├──────────────┤  │
│  │对话3  │          │  │              │  │
│  │...    │          │  │  消息列表     │  │
│  ├──────┤          │  │  (Markdown)  │  │
│  │新建对话│         │  │  (引用卡片)  │  │
│  └──────┘          │  │  (诊断流程)  │  │
│                    │  │              │  │
│                    │  ├──────────────┤  │
│                    │  │ 输入框 + 工具 │  │
│                    │  └──────────────┘  │
└──────────────────────────────────────────┘
```

## 13. 部署架构

### 13.1 Docker Compose (开发/小型部署)

```
services:
  nginx:          # 反向代理 + SSL termination
  fastapi:        # FastAPI + LangGraph
  celery-worker:  # 异步任务 (文档 ingestion)
  postgres:       # PostgreSQL + pgvector
  redis:          # 缓存 + 任务队列
  ollama:         # (可选) 本地模型
```

### 13.2 Kubernetes (生产部署)

```
ingress-nginx → fastapi (HPA, 2-10 replicas)
                                  ├── postgres (HA, Patroni)
                                  ├── redis (sentinel/cluster)
                                  ├── celery-worker
                                  ├── minio (文档存储)
                                  └── ollama (GPU node)
```

### 13.3 环境要求

- Python 3.12+
- PostgreSQL 16+ with pgvector
- Redis 7+
- Node.js 20+ (前端构建)
- Docker & Docker Compose

## 14. 质量保障

### 14.1 TDD 驱动开发规范

系统强制遵循 **Red-Green-Refactor** 循环，任何功能代码在测试通过之前不得合入。

```
┌─────────────────────────────────────────────────┐
│                 TDD 生命周期                      │
│                                                   │
│  RED: 编写失败的测试                                 │
│  │  ├─ 明确功能期望                                 │
│  │  ├─ 测试替身 (Mock/Stub/Fake)                   │
│  │  └─ 运行确认测试失败                             │
│  │                                                  │
│  GREEN: 编写最简实现代码                             │
│  │  ├─ 仅满足测试通过的量                            │
│  │  └─ 不允许超前设计                               │
│  │                                                  │
│  REFACTOR: 优化代码质量                              │
│     ├─ 消除重复 (DRY)                               │
│     ├─ 提升可读性                                   │
│     └─ 保持测试通过                                 │
└─────────────────────────────────────────────────────┘
```

### 14.2 可测试性架构设计

为实现 TDD，系统采用 **依赖注入** 模式，所有外部依赖均可替换为测试替身：

```python
# 依赖注入示意
class LLMService:
    def __init__(self, provider: LLMProvider):
        self._provider = provider  # 可注入 MockProvider

class KnowledgeService:
    def __init__(self, session: AsyncSession, llm: LLMService):
        self._session = session
        self._llm = llm
```

**测试替身层级**：

| 层级      | 测试替身          | 用途                             |
| --------- | ----------------- | -------------------------------- |
| LLM       | `MockLLMProvider` | 返回预设响应，不调用外部 API     |
| 数据库    | `test Session`    | 使用独立 test database，事务隔离 |
| Embedding | `MockEmbedding`   | 返回固定维度向量                 |
| 向量搜索  | `in-memory index` | 避免 pgvector 依赖               |

### 14.3 测试基础设施

```
backend/
└── tests/
    ├── conftest.py          # 全局 fixtures
    ├── factories.py         # 测试数据工厂
    ├── mock_providers.py    # Mock LLM/Embedding
    ├── test_config.py       # 配置测试
    ├── test_db/             # 数据库测试
    ├── test_services/       # 服务层测试
    ├── test_agents/         # Agent 测试
    └── test_api/            # API 测试
```

**conftest.py 核心 fixture 设计**：

```python
@pytest.fixture
async def db_session():
    """每个测试独立事务，自动回滚"""
    async with test_engine.connect() as conn:
        tx = await conn.begin()
        async with async_sessionmaker(conn) as session:
            yield session
        await tx.rollback()

@pytest.fixture
def mock_llm():
    """返回预设响应的 Mock LLM"""
    return MockLLMProvider(responses={
        "你好": "你好！有什么我可以帮助你的？",
        "default": "这是一个模拟回复",
    })

@pytest.fixture
def test_client(db_session, mock_llm):
    """注入测试替身的 FastAPI 客户端"""
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[LLMService] = lambda: mock_llm
    return TestClient(app)
```

### 14.4 测试类型与覆盖率目标

| 测试类型   | 框架                       | 目标覆盖率    | 说明                           |
| ---------- | -------------------------- | ------------- | ------------------------------ |
| 单元测试   | pytest + pytest-asyncio    | >= 90%        | 每 Agent/Service/Tool 独立测试 |
| 集成测试   | pytest + httpx.AsyncClient | >= 80%        | API 端点完整流程测试           |
| Agent 测试 | LangGraph 内置 tester      | 100% 核心路径 | Graph 节点/边/状态转换         |
| 前端测试   | Vitest + Testing Library   | >= 70%        | Component + Store 测试         |
| E2E 测试   | Playwright                 | 核心用户路径  | 完整对话流程                   |

### 14.5 TDD 执行规范

**每个开发任务的执行顺序**：

1. 编写测试文件（测试失败 → RED）
2. 确认测试因"功能未实现"而失败
3. 编写最简实现代码（测试通过 → GREEN）
4. 重构优化代码（REFACTOR）
5. 提交前运行完整测试套件，确保全部通过

**禁止行为**：

- ❌ 先写实现后写测试
- ❌ 提交未通过测试的代码
- ❌ 因测试难写而跳过测试
- ❌ 测试依赖外部 LLM API/真实数据库

### 14.2 可观测性指标

| 指标           | 告警阈值 | 说明         |
| -------------- | -------- | ------------ |
| LLM 错误率     | > 5%     | 模型调用失败 |
| P95 响应时间   | > 10s    | 用户体验     |
| Agent 成功率   | < 95%    | 完成任务比例 |
| 工具调用成功率 | < 90%    | 工具执行失败 |
| Token 消耗异常 | > 3σ     | 异常消耗检测 |

## 15. 迭代路线图

### Phase 1 (MVP - 4周)

- [ ] 测试基础设施 (pytest + conftest + Mock LLM + Mock DB)
- [ ] FastAPI 项目骨架 + 项目结构
- [ ] LLM Router + 单元测试
- [ ] PostgreSQL + pgvector + Alembic + 数据库测试
- [ ] LangGraph Supervisor Agent + Agent 测试
- [ ] Chat API (SSE 流式) + API 集成测试
- [ ] 知识库服务 + 服务层测试
- [ ] 基础聊天前端 (React + Redux Toolkit + Ant Design)
- [ ] Docker Compose 开发环境

### Phase 2 (核心能力 - 4周)

- [ ] Knowledge Agent (RAG)
- [ ] 文档 ingestion 管线
- [ ] 对话历史管理
- [ ] 知识库管理前端
- [ ] 引用溯源展示

### Phase 3 (Agent 体系 - 4周)

- [ ] Diagnosis Agent
- [ ] Escalation Agent
- [ ] Ticket Agent (内部工单)
- [ ] Data Agent
- [ ] 多 Agent 协作流程
- [ ] 人机协同 (Interrupt)

### Phase 4 (企业级 - 4周)

- [ ] Auth (OIDC/OAuth2) + RBAC
- [ ] 多租户数据隔离
- [ ] 审计日志
- [ ] OpenTelemetry + Prometheus
- [ ] LangSmith 评估
- [ ] 外部工单系统集成
- [ ] Kubernetes 部署配置

### Phase 5 (持续优化)

- [ ] 多模型 Fallback 策略
- [ ] Agent 回答质量评估
- [ ] A/B 测试框架
- [ ] 用户反馈闭环
- [ ] 常见问题自动学习
