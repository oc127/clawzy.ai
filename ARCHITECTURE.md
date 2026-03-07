# Clawzy.ai — 完整系统架构规划

> **Product**: OpenClaw-as-a-Service 平台
> **Domain**: clawzy.ai
> **Tagline**: Your AI Lobster, Any Brain.
> **Model**: Credits 积分制 + 三档订阅 ($9 / $19 / $39)
> **Tech Stack**: FastAPI · Next.js · PostgreSQL · Redis · Docker · LiteLLM · OpenClaw

---

## 1. 高层架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          用户设备 (Browser / Mobile)                     │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ HTTPS / WSS
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 0 — Edge / Gateway                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────────────────┐  │
│  │  Cloudflare   │  │  Nginx        │  │  Rate Limiter              │  │
│  │  CDN + DNS    │  │  Reverse Proxy│  │  (Redis-backed)            │  │
│  │  SSL Termination│ │  + WebSocket  │  │                            │  │
│  └───────────────┘  └───────┬───────┘  └────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                     ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Layer 1        │  │  Layer 2         │  │  Layer 3         │
│  Web App        │  │  Backend API     │  │  OpenClaw        │
│  (Next.js)      │  │  (FastAPI)       │  │  Runtime         │
│  :3000          │  │  :8000           │  │  (Docker)        │
└─────────────────┘  └──────────────────┘  └──────────────────┘
```

### 层级详解

| 层级 | 职责 | 技术 |
|------|------|------|
| **Layer 0 — Edge** | CDN、SSL、反向代理、WebSocket 转发、限流 | Cloudflare + Nginx + Redis |
| **Layer 1 — Web App** | 用户界面：注册/登录、聊天、Dashboard、设置、支付 | Next.js 14 (App Router) |
| **Layer 2 — Backend API** | 业务核心：认证、Credits 计费、容器编排、模型路由 | FastAPI + SQLAlchemy + Celery |
| **Layer 3 — OpenClaw Runtime** | 每用户一个 Agent 实例，持久运行 | OpenClaw Docker 容器 |

---

## 2. 项目目录结构

```
clawzy.ai/
├── ARCHITECTURE.md                  # 本文档
├── DEPLOY.md                        # 部署指南
├── docker-compose.yml               # PoC 部署编排 (已有)
├── docker-compose.prod.yml          # 生产部署编排
├── .env.example                     # 环境变量模板
├── .gitignore
│
├── backend/                         # ===== FastAPI 后端 =====
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口，挂载所有 router
│   │   ├── config.py                # Pydantic Settings，环境变量管理
│   │   ├── deps.py                  # 公共依赖 (get_db, get_current_user)
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM 模型
│   │   │   ├── user.py              # User, UserProfile
│   │   │   ├── subscription.py      # Subscription, Plan
│   │   │   ├── credits.py           # CreditBalance, CreditTransaction
│   │   │   ├── agent.py             # Agent (用户的 OpenClaw 实例)
│   │   │   └── chat.py              # Conversation, Message
│   │   │
│   │   ├── schemas/                 # Pydantic request/response 模型
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── agent.py
│   │   │   ├── chat.py
│   │   │   └── billing.py
│   │   │
│   │   ├── api/                     # API 路由
│   │   │   ├── v1/
│   │   │   │   ├── auth.py          # POST /register, /login, /refresh
│   │   │   │   ├── users.py         # GET /me, PATCH /me
│   │   │   │   ├── agents.py        # CRUD /agents, POST /agents/{id}/start|stop
│   │   │   │   ├── chat.py          # WebSocket /ws/chat/{agent_id}
│   │   │   │   ├── models.py        # GET /models (可用模型列表)
│   │   │   │   └── billing.py       # GET /credits, POST /checkout, webhooks
│   │   │   └── router.py            # 汇总所有 v1 路由
│   │   │
│   │   ├── services/                # 业务逻辑层
│   │   │   ├── auth_service.py      # 注册、登录、JWT
│   │   │   ├── agent_service.py     # 容器创建、启停、健康检查
│   │   │   ├── chat_service.py      # 消息转发、流式输出
│   │   │   ├── credits_service.py   # 积分扣费、余额查询、用量统计
│   │   │   ├── model_service.py     # LiteLLM 交互、模型列表
│   │   │   └── billing_service.py   # Stripe 订阅、支付、Webhook
│   │   │
│   │   ├── core/                    # 基础设施
│   │   │   ├── security.py          # JWT 签发/验证、密码哈希
│   │   │   ├── database.py          # SQLAlchemy async engine + session
│   │   │   ├── redis.py             # Redis 连接池
│   │   │   └── docker_manager.py    # Docker SDK，容器生命周期管理
│   │   │
│   │   └── workers/                 # 异步任务 (Celery)
│   │       ├── celery_app.py        # Celery 配置
│   │       ├── agent_tasks.py       # 容器启停、健康巡检
│   │       └── billing_tasks.py     # 定时扣费、用量统计
│   │
│   ├── alembic/                     # 数据库迁移
│   │   ├── alembic.ini
│   │   └── versions/
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_agents.py
│   │   ├── test_credits.py
│   │   └── test_chat.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── web/                             # ===== Next.js 前端 =====
│   ├── src/
│   │   ├── app/                     # App Router 页面
│   │   │   ├── layout.tsx           # 全局 Layout
│   │   │   ├── page.tsx             # Landing Page
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx       # Dashboard sidebar layout
│   │   │   │   ├── page.tsx         # Dashboard 首页 (Agent 概览)
│   │   │   │   ├── chat/[agentId]/page.tsx   # 聊天界面
│   │   │   │   ├── agents/page.tsx  # Agent 管理
│   │   │   │   ├── models/page.tsx  # 模型选择
│   │   │   │   ├── billing/page.tsx # 积分 + 订阅管理
│   │   │   │   └── settings/page.tsx# 账户设置
│   │   │   └── api/                 # Next.js API routes (BFF)
│   │   │       └── [...proxy]/route.ts  # 代理到 FastAPI
│   │   │
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx   # 聊天窗口主组件
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   └── StreamingText.tsx# 流式输出
│   │   │   ├── dashboard/
│   │   │   │   ├── AgentCard.tsx    # Agent 状态卡片
│   │   │   │   ├── CreditsBadge.tsx # 积分余额显示
│   │   │   │   └── UsageChart.tsx   # 用量图表
│   │   │   ├── ui/                  # 基础 UI 组件 (shadcn/ui)
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Header.tsx
│   │   │       └── MobileNav.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts              # Axios/fetch 封装
│   │   │   ├── ws.ts               # WebSocket 客户端
│   │   │   ├── auth.ts             # JWT token 管理
│   │   │   └── credits.ts          # 积分换算工具函数
│   │   │
│   │   └── hooks/
│   │       ├── useAuth.ts
│   │       ├── useChat.ts          # WebSocket 聊天 hook
│   │       ├── useCredits.ts
│   │       └── useAgent.ts
│   │
│   ├── public/
│   │   └── logo.svg
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.ts
│
├── litellm/                         # ===== LiteLLM 模型路由 (已有) =====
│   └── config.yaml
│
├── openclaw/                        # ===== OpenClaw 配置模板 (已有) =====
│   └── openclaw.json
│
├── nginx/                           # ===== Nginx 反向代理 =====
│   ├── nginx.conf
│   └── conf.d/
│       └── clawzy.conf              # server block: 路由到各服务
│
└── scripts/                         # ===== 运维脚本 =====
    ├── setup-server.sh              # 服务器初始化 (已有)
    ├── smoke-test.sh                # 冒烟测试 (已有)
    ├── backup-db.sh                 # PostgreSQL 备份
    └── deploy.sh                    # 生产部署脚本
```

---

## 3. 数据库设计 (PostgreSQL)

### 3.1 ER 关系图

```
┌──────────┐     ┌──────────────┐     ┌───────────────┐
│  users   │────<│ subscriptions│     │  credit_txns  │
│          │     │              │     │               │
│ id (PK)  │     │ user_id (FK) │     │ user_id (FK)  │
│ email    │     │ plan         │     │ amount (+/-)  │
│ name     │     │ stripe_sub_id│     │ reason        │
│ password │     │ status       │     │ model_name    │
│ created  │     │ current_end  │     │ tokens_used   │
└────┬─────┘     └──────────────┘     │ created       │
     │                                └───────────────┘
     │
     │     ┌──────────────┐     ┌────────────────┐
     └────<│   agents     │────<│ conversations  │
           │              │     │                │
           │ user_id (FK) │     │ agent_id (FK)  │
           │ name         │     │ title          │
           │ model_name   │     │ created        │
           │ container_id │     └───────┬────────┘
           │ status       │             │
           │ config (JSON)│             │
           └──────────────┘     ┌───────▼────────┐
                                │   messages     │
                                │                │
                                │ conv_id (FK)   │
                                │ role           │
                                │ content        │
                                │ tokens_in      │
                                │ tokens_out     │
                                │ credits_used   │
                                │ model_name     │
                                │ created        │
                                └────────────────┘
```

### 3.2 核心表定义

#### users
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | 用户 ID |
| email | VARCHAR(255) UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| name | VARCHAR(100) | 显示名 |
| avatar_url | VARCHAR(500) | 头像 |
| credit_balance | INTEGER DEFAULT 500 | 当前积分余额 (注册送 500) |
| stripe_customer_id | VARCHAR(255) | Stripe 客户 ID |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

#### subscriptions
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| plan | ENUM('free','starter','pro','business') | 套餐 |
| stripe_subscription_id | VARCHAR(255) | Stripe 订阅 ID |
| status | ENUM('active','canceled','past_due') | 状态 |
| current_period_start | TIMESTAMPTZ | 当前计费周期开始 |
| current_period_end | TIMESTAMPTZ | 当前计费周期结束 |
| credits_included | INTEGER | 本周期包含积分 |
| credits_reset_at | TIMESTAMPTZ | 积分重置时间 |

#### agents
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| name | VARCHAR(100) | Agent 昵称 |
| model_name | VARCHAR(50) | 当前使用模型 (如 deepseek-chat) |
| container_id | VARCHAR(100) | Docker 容器 ID |
| status | ENUM('creating','running','stopped','error') | 状态 |
| config | JSONB | OpenClaw 配置覆盖 |
| ws_port | INTEGER | 分配的 WebSocket 端口 |
| created_at | TIMESTAMPTZ | |
| last_active_at | TIMESTAMPTZ | 最后活跃时间 |

#### credit_transactions
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| amount | INTEGER | 变动量 (正=充值/赠送, 负=消耗) |
| balance_after | INTEGER | 变动后余额 |
| reason | ENUM('signup_bonus','subscription','topup','usage','refund') | |
| model_name | VARCHAR(50) | 消耗时用的模型 |
| tokens_input | INTEGER | 模型输入 token 数 |
| tokens_output | INTEGER | 模型输出 token 数 |
| agent_id | UUID (FK → agents) | 关联的 Agent |
| created_at | TIMESTAMPTZ | |

#### conversations
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| agent_id | UUID (FK → agents) | |
| title | VARCHAR(200) | 对话标题 (自动生成) |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

#### messages
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| conversation_id | UUID (FK → conversations) | |
| role | ENUM('user','assistant','system') | |
| content | TEXT | 消息内容 |
| tokens_input | INTEGER | |
| tokens_output | INTEGER | |
| credits_used | INTEGER | 本次消耗积分 |
| model_name | VARCHAR(50) | 本次使用的模型 |
| created_at | TIMESTAMPTZ | |

---

## 4. API 设计

### 4.1 认证 (Auth)

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/auth/register` | 注册，自动送 500 Credits |
| POST | `/api/v1/auth/login` | 登录，返回 JWT |
| POST | `/api/v1/auth/refresh` | 刷新 token |
| POST | `/api/v1/auth/logout` | 登出 (可选，前端清 token 即可) |

#### 注册流程

```
Client                     Backend                   Database
  │  POST /register          │                          │
  │  {email, password, name} │                          │
  │ ─────────────────────────▶                          │
  │                          │  创建 user               │
  │                          │  credit_balance = 500    │
  │                          │  插入 credit_txn         │
  │                          │  (signup_bonus, +500)    │
  │                          │ ─────────────────────────▶
  │                          │                          │
  │  {access_token, user}    │                          │
  │ ◀─────────────────────────                          │
```

### 4.2 Agent 管理

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/agents` | 列出我的所有 Agent |
| POST | `/api/v1/agents` | 创建 Agent (选模型，起容器) |
| GET | `/api/v1/agents/{id}` | Agent 详情 + 状态 |
| PATCH | `/api/v1/agents/{id}` | 修改 Agent (换模型、改名) |
| DELETE | `/api/v1/agents/{id}` | 删除 Agent (停容器) |
| POST | `/api/v1/agents/{id}/start` | 启动 Agent |
| POST | `/api/v1/agents/{id}/stop` | 停止 Agent |

#### 创建 Agent 流程

```
Client                     Backend                   Docker
  │  POST /agents            │                          │
  │  {name, model_name}      │                          │
  │ ─────────────────────────▶                          │
  │                          │  检查套餐 agent 数量限制  │
  │                          │  分配 ws_port             │
  │                          │  docker create container  │
  │                          │ ─────────────────────────▶
  │                          │  container_id             │
  │                          │ ◀─────────────────────────
  │                          │  写入 openclaw.json       │
  │                          │  docker start             │
  │                          │ ─────────────────────────▶
  │  {agent: {id, status:    │                          │
  │   "creating"}}           │                          │
  │ ◀─────────────────────────                          │
  │                          │                          │
  │  (polling / ws 通知)     │  container healthy →     │
  │  {status: "running"}     │  更新 agent.status       │
  │ ◀─────────────────────────                          │
```

### 4.3 聊天 (Chat)

| Method | Path | 说明 |
|--------|------|------|
| WebSocket | `/api/v1/ws/chat/{agent_id}` | 实时聊天 (主通道) |
| GET | `/api/v1/agents/{id}/conversations` | 对话列表 |
| GET | `/api/v1/conversations/{id}/messages` | 历史消息 |

#### WebSocket 聊天流程

```
Client                   Backend                 OpenClaw         LiteLLM
  │  ws://connect          │                        │                │
  │  + JWT token           │                        │                │
  │ ───────────────────────▶                        │                │
  │                        │  验证 JWT               │                │
  │                        │  检查 credit_balance    │                │
  │  connected ✓           │                        │                │
  │ ◀───────────────────────                        │                │
  │                        │                        │                │
  │  {type: "message",     │                        │                │
  │   content: "你好"}     │                        │                │
  │ ───────────────────────▶                        │                │
  │                        │  转发到 OpenClaw WS     │                │
  │                        │ ───────────────────────▶                │
  │                        │                        │  LLM 调用       │
  │                        │                        │ ───────────────▶
  │                        │                        │  stream chunks  │
  │                        │                        │ ◀───────────────
  │                        │  stream chunks          │                │
  │  {type: "stream",      │ ◀───────────────────────                │
  │   content: "你"}       │                        │                │
  │ ◀───────────────────────                        │                │
  │  {type: "stream",      │                        │                │
  │   content: "好"}       │                        │                │
  │ ◀───────────────────────                        │                │
  │  ...                   │                        │                │
  │  {type: "done",        │  收到 usage 信息        │                │
  │   usage: {credits: 3}} │  扣 credits             │                │
  │ ◀───────────────────────  记录 message + txn     │                │
```

### 4.4 模型

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/models` | 可用模型列表 (含积分消耗估算) |

响应示例:
```json
{
  "models": [
    {
      "id": "deepseek-chat",
      "name": "DeepSeek V3",
      "provider": "DeepSeek",
      "tier": "standard",
      "credits_per_1k_input": 0.1,
      "credits_per_1k_output": 0.2,
      "description": "高性价比通用模型"
    },
    {
      "id": "claude-sonnet",
      "name": "Claude Sonnet",
      "provider": "Anthropic",
      "tier": "premium",
      "credits_per_1k_input": 2.0,
      "credits_per_1k_output": 10.0,
      "description": "顶级推理能力"
    }
  ]
}
```

### 4.5 计费 (Billing)

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/credits` | 积分余额 + 本周期用量 |
| GET | `/api/v1/credits/transactions` | 积分流水 |
| GET | `/api/v1/billing/plans` | 套餐列表 |
| POST | `/api/v1/billing/checkout` | 创建 Stripe Checkout Session |
| POST | `/api/v1/billing/portal` | 创建 Stripe Customer Portal |
| POST | `/api/v1/webhooks/stripe` | Stripe Webhook 回调 |

---

## 5. Credits 积分系统

### 5.1 积分换算规则

积分的核心逻辑：**1 Credit ≈ ¥0.01 模型成本**。不同模型按实际成本换算。

| 模型 | Input (Credits/1K tokens) | Output (Credits/1K tokens) | 类型 |
|------|---------------------------|----------------------------|------|
| DeepSeek V3 Chat | 0.1 | 0.2 | Standard |
| DeepSeek R1 | 0.4 | 2.0 | Premium |
| Qwen Turbo | 0.05 | 0.1 | Standard |
| Qwen Plus | 0.1 | 0.2 | Standard |
| Qwen Max | 0.3 | 0.6 | Standard |
| Claude Sonnet | 2.0 | 10.0 | Premium |
| Claude Haiku | 0.5 | 1.5 | Premium |
| GPT-4o | 1.5 | 8.0 | Premium |
| GPT-4o Mini | 0.1 | 0.3 | Standard |
| Gemini Flash | 0.05 | 0.15 | Standard |

### 5.2 套餐定义

| 套餐 | 月费 | 包含 Credits | Agent 数 | 超额价格 |
|------|------|-------------|---------|----------|
| Free (试用) | $0 | 500 (一次性) | 1 | 不可超额 |
| Starter | $9 | 3,000/月 | 1 | $5/1000 Credits |
| Pro | $19 | 8,000/月 | 3 | $5/1000 Credits |
| Business | $39 | 20,000/月 | 10 | $4/1000 Credits |

### 5.3 扣费流程

```python
# 伪代码: 每次 LLM 调用后扣费
def deduct_credits(user_id, model_name, tokens_in, tokens_out):
    rate = CREDIT_RATES[model_name]
    credits_used = (
        tokens_in / 1000 * rate.input +
        tokens_out / 1000 * rate.output
    )
    credits_used = max(1, round(credits_used))  # 最低 1 Credit

    user = get_user(user_id)
    if user.credit_balance < credits_used:
        raise InsufficientCreditsError()

    user.credit_balance -= credits_used
    create_transaction(
        user_id=user_id,
        amount=-credits_used,
        balance_after=user.credit_balance,
        reason="usage",
        model_name=model_name,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
    )
    return credits_used
```

---

## 6. 容器编排 (Multi-Tenant)

### 6.1 MVP 方案：Docker SDK 直接管理

MVP 阶段不上 K8s，用 Python Docker SDK (`docker` package) 直接管理容器。

```python
# 伪代码: AgentService
import docker

class AgentService:
    def __init__(self):
        self.client = docker.from_env()

    def create_agent(self, user_id, agent_id, model_name) -> str:
        """为用户创建一个 OpenClaw 容器"""
        ws_port = self.allocate_port()

        # 生成该用户专属的 openclaw.json
        config = generate_openclaw_config(model_name)

        container = self.client.containers.run(
            image="ghcr.io/openclaw/openclaw:latest",
            name=f"clawzy-agent-{agent_id}",
            detach=True,
            restart_policy={"Name": "unless-stopped"},
            environment={
                "OPENCLAW_GATEWAY_TOKEN": generate_token(),
            },
            ports={
                "18789/tcp": ("127.0.0.1", ws_port),
            },
            mem_limit="512m",
            cpu_quota=50000,  # 0.5 CPU
            network="clawzy-network",
            labels={
                "clawzy.user_id": str(user_id),
                "clawzy.agent_id": str(agent_id),
            },
        )
        return container.id

    def stop_agent(self, container_id):
        container = self.client.containers.get(container_id)
        container.stop(timeout=10)

    def remove_agent(self, container_id):
        container = self.client.containers.get(container_id)
        container.remove(force=True)

    def get_agent_status(self, container_id) -> str:
        container = self.client.containers.get(container_id)
        return container.status  # running, exited, etc.
```

### 6.2 资源限制 (per container)

| 资源 | 限制 | 说明 |
|------|------|------|
| 内存 | 512MB | OpenClaw 不开浏览器够用 |
| CPU | 0.5 核 | 大部分时间等 API 响应，CPU 不密集 |
| 磁盘 | Volume 挂载 | 对话记忆存 volume |
| 网络 | clawzy-network | 容器间通信走内部网络 |

### 6.3 端口分配

每个 Agent 容器需要一个唯一的 WebSocket 端口，后端维护端口池：

```
端口范围: 19000 - 19999
每个用户的每个 Agent 分配一个端口
Agent 删除后端口回收
```

### 6.4 健康巡检 (Celery Beat)

```
每 60 秒:
  遍历所有 status='running' 的 agent
  检查容器是否存活
  如果容器挂了 → 自动重启
  如果重启 3 次仍失败 → 标记 status='error'，通知用户
```

### 6.5 未来演进：Kubernetes

当用户超过 100-200 人，迁移到 K8s：
- 每个 Agent = 一个 Pod
- 用 Deployment 管理滚动更新
- HPA 自动扩缩
- 多节点分布式

MVP 阶段不需要，架构预留即可（service 层抽象，不直接依赖 Docker SDK）。

---

## 7. 模型路由 (LiteLLM)

### 7.1 架构

```
Backend (FastAPI)
    │
    │ OpenAI-compatible API
    ▼
┌──────────────────────────────────────┐
│           LiteLLM Proxy              │
│                                      │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ Router   │  │ Usage Tracking   │  │
│  │          │  │ (callbacks)      │  │
│  └────┬─────┘  └──────────────────┘  │
│       │                              │
│  ┌────┼──────────┬──────────┐        │
│  │    │          │          │        │
│  ▼    ▼          ▼          ▼        │
│ DeepSeek  Qwen  Claude   GPT-4o     │
│ API       API   API      API        │
└──────────────────────────────────────┘
```

### 7.2 LiteLLM 已配置模型 (PoC)

- DeepSeek V3 Chat, R1 Reasoner
- Qwen Max, Plus, Turbo

### 7.3 待添加模型 (MVP 后)

- Claude Sonnet, Haiku (Anthropic API)
- GPT-4o, GPT-4o Mini (OpenAI API)
- Gemini Flash, Pro (Google AI)
- Llama, Mistral (via Groq/Together)

### 7.4 Usage Callback ✅

LiteLLM `success_callback` 在每次模型请求完成后回调后端，报告精确 token 用量：

```yaml
# litellm/config.yaml（已配置）
litellm_settings:
  success_callback: ["custom_callback_api"]
  custom_callback_api_url: "http://clawzy-backend:8000/api/v1/internal/usage-callback"
```

**双通道去重计费架构**（风险 D-2 解决方案）：

```
LiteLLM Proxy                          Backend
     │                                    │
     │  success_callback POST              │
     │  {call_id, model, usage, metadata}  │
     │ ──────────────────────────────────▶  │
     │                                    │  Redis SETNX clawzy:usage:dedup:{call_id}
     │                                    │  如果设置成功 → deduct_credits()
     │                                    │  如果已存在 → skip（ws_relay 已扣过）
     │                                    │
OpenClaw Container ──── done event ────▶ ws_relay
                                          │  提取 call_id
                                          │  Redis SETNX 尝试
                                          │  成功 → deduct_credits()
                                          │  失败 → skip（callback 已扣过）
```

- **主通道**：LiteLLM callback → `/internal/usage-callback`（精确 token 数）
- **兜底通道**：ws_relay 拦截 `done` 事件（容器报告的 token 数）
- **去重机制**：Redis `SETNX` 按 `call_id` 保证同一请求只扣一次
- **TTL**：去重 key 24 小时后自动清理

---

## 8. 实时聊天架构

### 8.1 WebSocket 链路

```
Browser                  Nginx              FastAPI            OpenClaw Container
   │                       │                   │                      │
   │  wss://clawzy.ai/     │                   │                      │
   │  ws/chat/{agent_id}   │                   │                      │
   │ ──────────────────────▶                   │                      │
   │                       │  proxy_pass       │                      │
   │                       │ ─────────────────▶│                      │
   │                       │                   │  验证 JWT            │
   │                       │                   │  查询 agent → port   │
   │                       │                   │  ws://127.0.0.1:     │
   │                       │                   │  {port}/ws           │
   │                       │                   │ ─────────────────────▶
   │                       │                   │                      │
   │  双向消息流 ◀──────────────────────────────────────────────────────▶
```

### 8.2 消息协议 (Client ↔ Backend)

```typescript
// 客户端发送
{ type: "message", content: "你好" }
{ type: "switch_model", model: "claude-sonnet" }

// 服务端推送
{ type: "stream", content: "你" }          // 流式文本片段
{ type: "stream", content: "好" }
{ type: "done", usage: { credits: 3, balance: 497 } }
{ type: "error", code: "insufficient_credits", message: "积分不足" }
{ type: "agent_status", status: "running" }
```

---

## 9. Nginx 反向代理

```nginx
# nginx/conf.d/clawzy.conf

upstream backend {
    server 127.0.0.1:8000;
}

upstream webapp {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name clawzy.ai www.clawzy.ai;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name clawzy.ai www.clawzy.ai;

    # SSL certs (Let's Encrypt / Cloudflare Origin)
    ssl_certificate     /etc/ssl/clawzy/cert.pem;
    ssl_certificate_key /etc/ssl/clawzy/key.pem;

    # API 路由 → FastAPI
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 聊天 → FastAPI (再由 FastAPI 转发到 OpenClaw 容器)
    location /api/v1/ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Stripe Webhook
    location /api/v1/webhooks/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
    }

    # 其他所有请求 → Next.js
    location / {
        proxy_pass http://webapp;
        proxy_set_header Host $host;
    }
}
```

---

## 10. 生产 Docker Compose

```yaml
# docker-compose.prod.yml (概念设计)
services:
  # --- 数据层 ---
  postgres:
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["127.0.0.1:5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["127.0.0.1:6379:6379"]

  # --- 模型路由 ---
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    depends_on: [postgres]
    volumes: [./litellm/config.yaml:/app/config.yaml]
    ports: ["127.0.0.1:4000:4000"]

  # --- 后端 API ---
  backend:
    build: ./backend
    depends_on: [postgres, redis, litellm]
    volumes: [/var/run/docker.sock:/var/run/docker.sock]  # 管理容器
    ports: ["127.0.0.1:8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://...
      REDIS_URL: redis://redis:6379/0
      LITELLM_URL: http://litellm:4000
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
      JWT_SECRET: ${JWT_SECRET}

  # --- Celery Worker (异步任务) ---
  celery-worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker -l info
    depends_on: [postgres, redis]
    volumes: [/var/run/docker.sock:/var/run/docker.sock]

  # --- Celery Beat (定时任务) ---
  celery-beat:
    build: ./backend
    command: celery -A app.workers.celery_app beat -l info
    depends_on: [redis]

  # --- 前端 ---
  web:
    build: ./web
    ports: ["127.0.0.1:3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: https://clawzy.ai/api

  # --- 反向代理 ---
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/ssl/clawzy
    depends_on: [backend, web]

# 注意: OpenClaw 用户容器由 backend 通过 Docker SDK 动态创建
# 不在此 compose 文件中静态定义
```

---

## 11. 安全设计

| 层面 | 措施 |
|------|------|
| **认证** | JWT (access 15min + refresh 7d)，bcrypt 密码哈希 |
| **传输** | Cloudflare SSL + Nginx HTTPS，全链路加密 |
| **API** | Rate limiting (Redis)，CORS 白名单 |
| **容器隔离** | 每用户独立容器，mem/cpu limit，独立 network namespace |
| **数据** | PostgreSQL 数据加密，.env 600 权限，secrets 不入 git |
| **支付** | Stripe Webhook 签名验证，不存信用卡信息 |
| **Docker Socket** | 后端挂载 docker.sock 是必要的但有风险，生产环境考虑用 Docker API over TCP + TLS |

---

## 12. MVP 开发顺序 (6 周)

### Week 1 — 基础设施 ✅ (部分完成)
- [x] Docker Compose (PostgreSQL + LiteLLM + OpenClaw)
- [x] LiteLLM 模型配置 (DeepSeek + Qwen)
- [x] 服务器初始化脚本
- [ ] Nginx 反向代理 + SSL
- [ ] Redis 加入 Compose

### Week 2 — 后端核心
- [ ] FastAPI 项目骨架
- [ ] 数据库模型 + Alembic 迁移
- [ ] 认证系统 (注册/登录/JWT)
- [ ] Agent CRUD + 容器管理 (Docker SDK)
- [ ] Credits 积分扣费

### Week 3 — 聊天链路
- [ ] WebSocket 聊天端点
- [ ] Backend ↔ OpenClaw 容器消息转发
- [ ] 流式输出
- [ ] 消息持久化 + 对话历史
- [ ] LiteLLM usage callback → Credits 扣费

### Week 4 — 前端 MVP
- [ ] Next.js 项目骨架 (shadcn/ui + Tailwind)
- [ ] Landing Page
- [ ] 注册/登录页
- [ ] Dashboard (Agent 列表)
- [ ] 聊天界面 (WebSocket)
- [ ] 模型选择

### Week 5 — 支付 + 打磨
- [ ] Stripe 集成 (Checkout + Customer Portal + Webhook)
- [ ] 积分余额 + 用量展示
- [ ] Agent 启停控制
- [ ] 错误处理 + 断线重连
- [ ] 移动端响应式

### Week 6 — 上线
- [ ] 阿里云新加坡 ECS 部署
- [ ] Cloudflare DNS + SSL
- [ ] 域名配置 (clawzy.ai)
- [ ] 冒烟测试
- [ ] Product Hunt / V2EX / 即刻发布
- [ ] 监控 + 日志 (可选: Grafana)

---

## 13. 技术栈总结

| 类别 | 技术 | 理由 |
|------|------|------|
| **后端框架** | FastAPI | 异步、类型安全、WebSocket 原生支持 |
| **ORM** | SQLAlchemy 2.0 (async) | Python 生态最成熟 |
| **数据库** | PostgreSQL 16 | 可靠、JSONB 支持、LiteLLM 也用 |
| **缓存/消息** | Redis 7 | Rate limiting、Celery broker、session |
| **异步任务** | Celery + Redis | 容器巡检、定时扣费 |
| **前端** | Next.js 14 (App Router) | SSR、文件路由、Vercel 生态 |
| **UI 库** | shadcn/ui + Tailwind CSS | 最快出活的组合 |
| **模型路由** | LiteLLM Proxy | 统一 10+ 模型供应商 |
| **AI 引擎** | OpenClaw | 龙虾本体 |
| **容器** | Docker + Docker SDK | MVP 够用，后期可迁 K8s |
| **支付** | Stripe | 全球收款、订阅管理 |
| **反向代理** | Nginx | WebSocket 支持、SSL |
| **CDN/DNS** | Cloudflare | 免费、快 |
| **服务器** | 阿里云 ECS 新加坡 | 低延迟、靠近用户 |

---

## 14. 全面风险清单 & 应对策略

> **原则**：风险不可消除，只能管理。MVP 阶段接受部分风险，但必须清楚知道自己在赌什么。

---

### 14.1 基础设施风险 (Infrastructure)

| # | 风险 | 严重度 | 概率 | 影响 | 应对策略 |
|---|------|--------|------|------|----------|
| I-1 | **单机单点故障** — 所有服务跑在一台 4C8G ECS 上，任何组件崩溃影响全站 | 🔴 高 | 中 | 全站不可用 | MVP 阶段接受。部署 Systemd watchdog + Docker restart policy。用户超 50 人后拆分为多节点 |
| I-2 | **Docker socket 挂载** — 后端容器挂载 `/var/run/docker.sock`，等于拥有宿主机 root 权限 | 🔴 高 | 低 | 宿主机被完全控制 | MVP 用 socket，生产切换 Docker API over TCP + TLS mutual auth。限制后端容器的 capabilities |
| I-3 | ~~**无灾备/备份**~~ — ✅ **已实现：pg_dump 每 6h → OSS** | 🟢 已解决 | — | — | **已实现**：`pg_dump` 每 6h cron → gzip → S3 兼容 API 上传 OSS（纯 curl+openssl，零额外依赖）。本地 14 天 + OSS 30 天自动清理。失败 webhook 告警。含 `restore-db.sh` 一键恢复。后期可上 pg_basebackup 流复制 |
| I-4 | **单可用区** — 新加坡单区部署，该区故障则全站宕机 | 🟡 中 | 低 | 数小时不可用 | MVP 接受。用户超 200 后做多 AZ 部署 |
| I-5 | **SSL 证书续期失败** — Let's Encrypt 证书 90 天过期，自动续期可能静默失败 | 🟡 中 | 中 | HTTPS 不可用 | certbot renew cron + 监控证书过期时间，过期前 14 天报警 |
| I-6 | **阿里云供应商锁定** — 深度依赖阿里云 ECS/OSS | 🟢 低 | — | 迁移成本高 | 全部用 Docker 部署，OSS 用 S3 兼容 API，保留迁移能力 |

---

### 14.2 容器编排风险 (Container Orchestration)

| # | 风险 | 严重度 | 概率 | 影响 | 应对策略 |
|---|------|--------|------|------|----------|
| C-1 | **单机容器密度天花板** — 4C8G 机器，每容器 0.5C+512MB，理论上限 ~16 个活跃 Agent | 🔴 高 | 高 | 无法承接新用户 | 这是 MVP 的硬约束。用户超 15 人时必须：① 升级机器规格 ② 加节点 ③ 上 K8s |
| C-2 | **端口池耗尽** — 19000-19999 只有 1000 个端口 | 🟡 中 | 低 | 无法创建新 Agent | 短期够用。长期改为 Unix socket 或 overlay network 内部路由，不占宿主机端口 |
| C-3 | **容器冷启动慢** — OpenClaw 镜像可能 500MB+，首次拉取 + 启动可能需要 30-60 秒 | 🟡 中 | 高 | 用户等待体验差 | 预拉镜像；注册后台异步创建容器；前端展示创建进度动画 |
| C-4 | **容器崩溃发现延迟** — Celery Beat 60 秒巡检一次，最坏情况用户等 60 秒才知道 Agent 挂了 | 🟡 中 | 中 | 用户消息发出去没回应 | WebSocket 断开即触发重连检查，不依赖定时巡检。加 Docker event stream 实时监听容器状态变化 |
| C-5 | **容器间网络未隔离** — 所有容器在同一个 `clawzy-network`，理论上容器间可互相访问 | 🟡 中 | 低 | 用户数据泄露 | 每用户创建独立 Docker network，或用 network policy 限制容器间通信 |
| C-6 | **僵尸容器堆积** — 用户注销/过期后容器没清理 | 🟡 中 | 中 | 资源浪费、端口泄漏 | 定时任务清理：Free 用户 7 天不活跃 → 停止容器；30 天 → 删除容器 |

---

### 14.3 数据与安全风险 (Data & Security)

| # | 风险 | 严重度 | 概率 | 影响 | 应对策略 |
|---|------|--------|------|------|----------|
| D-1 | ~~**积分扣费竞态条件**~~ — ✅ **已解决：`SELECT FOR UPDATE` 行锁** | 🟢 已解决 | — | — | **已实现**：`credits_service.deduct_credits()` 使用 `SELECT ... FOR UPDATE` 行锁防止并发扣成负数 |
| D-2 | ~~**LiteLLM usage callback 丢失**~~ — ✅ **已实现：双通道去重扣费** | 🟢 已解决 | — | — | **已实现**：LiteLLM `success_callback` → `/internal/usage-callback` 为主通道（精确 token 用量），ws_relay `done` 事件为兜底通道。两者通过 Redis `SETNX` 按 `call_id` 去重，保证只扣一次 |
| D-3 | **JWT token 泄露** — access token 被截获 | 🟡 中 | 低 | 账户被盗用 | access token 15 分钟过期；refresh token 绑定 IP/设备；敏感操作要求二次验证 |
| D-4 | **用户对话数据隐私** — 不同地区对 AI 对话数据有不同法规 (GDPR、PDPA 等) | 🟡 中 | — | 法律风险 | 明确隐私政策；提供数据导出/删除功能；新加坡 PDPA 合规先行，后续按目标市场补充 |
| D-5 | **容器内数据持久化** — 用户记忆 (MEMORY.md) 存在容器 volume，宿主机磁盘损坏则丢失 | 🟡 中 | 低 | 用户记忆丢失 | Volume 数据定期同步到 OSS；关键记忆同时写入 PostgreSQL |
| D-6 | **Redis 无持久化** — 默认配置重启后数据丢失（session、rate limit 状态） | 🟢 低 | 中 | 用户需重新登录；短暂限流失效 | 开启 Redis AOF 持久化；session 数据不仅存 Redis 也要能从 JWT 恢复 |
| D-7 | **内容安全** — 用户通过 Agent 生成违法/有害内容 | 🟡 中 | 中 | 平台法律责任 | 接入模型供应商自带的安全过滤；记录 audit log；用户协议明确责任划分 |

---

### 14.4 聊天链路风险 (Chat Pipeline)

| # | 风险 | 严重度 | 概率 | 影响 | 应对策略 |
|---|------|--------|------|------|----------|
| W-1 | **WebSocket 连接数上限** — Nginx/FastAPI 并发 WS 连接数受文件描述符和内存限制 | 🟡 中 | 中 | 新用户无法连接 | Nginx `worker_connections` 调高；FastAPI 异步处理；单机 ~1000 WS 没问题，瓶颈在容器数而非连接数 |
| W-2 | **流式输出中途断开** — 模型 API 返回一半时网络中断，token 已消耗但用户没收到完整回复 | 🟡 中 | 中 | 用户积分白花了 | 后端缓存完整流式内容；断线重连后可续传；只在完整接收后才扣费（或部分扣费） |
| W-3 | **消息顺序错乱** — WebSocket 消息乱序，尤其在弱网环境 | 🟢 低 | 低 | 对话上下文混乱 | 每条消息加序列号 (seq)，客户端按序重组 |
| W-4 | **Backend ↔ OpenClaw 双跳延迟** — 用户消息经 Nginx → FastAPI → OpenClaw → LiteLLM，链路过长 | 🟡 中 | 高 | 首 token 延迟高 | 监控 TTFT (Time To First Token)；长期考虑让 OpenClaw 直连 LiteLLM，减少一跳 |

---

### 14.5 外部依赖风险 (External Dependencies)

| # | 风险 | 严重度 | 概率 | 影响 | 应对策略 |
|---|------|--------|------|------|----------|
| E-1 | **OpenClaw 上游 breaking change** — 新版本不兼容现有配置 | 🔴 高 | 中 | 所有 Agent 崩溃 | 锁定镜像版本 tag，不用 `latest`；设置 staging 环境先测再升；维护 fork 做必要 patch |
| E-2 | **LiteLLM 上游 breaking change** — API 格式变化或 bug | 🟡 中 | 中 | 模型路由中断 | 同样锁定版本；关注 release notes；保留直连模型 API 的降级方案 |
| E-3 | **模型供应商 API 宕机** — DeepSeek/Qwen 等 API 不可用 | 🟡 中 | 中 | 用户无法聊天 | 同模型多供应商备份（如 DeepSeek 官方 + 第三方代理）；LiteLLM fallback 路由配置 |
| E-4 | **模型 API 涨价** — 供应商随时可能调价 | 🟡 中 | 高 | 毛利压缩甚至亏损 | Credits 换算表与模型成本解耦，可随时调整；定期审查定价；积分价格留有 30%+ 毛利空间 |
| E-5 | ~~**OpenClaw 开源协议风险**~~ — ✅ **已确认：MIT License，允许商业化** | 🟢 已解决 | — | — | **已确认 2025-03：OpenClaw 采用 MIT License（Copyright Peter Steinberger）**，完全允许商用包装、SaaS 分发、修改再许可。合规动作：① THIRD_PARTY_LICENSES 已添加 ② ToS/Privacy Policy 已添加开源归属声明 ③ 页脚已添加 OpenClaw 链接 |
| E-6 | **Cloudflare 免费计划限制** — 流量突增可能触发 Cloudflare 限制 | 🟢 低 | 低 | CDN 降级 | 监控 Cloudflare dashboard；预算内可升级到 Pro ($20/月) |

---

### 14.6 业务与合规风险 (Business & Compliance)

| # | 风险 | 严重度 | 概率 | 影响 | 应对策略 |
|---|------|--------|------|------|----------|
| B-1 | **Stripe 地域限制** — 部分目标市场国家不支持 Stripe 收款 | 🟡 中 | 高 | 丢失部分市场 | 东南亚/中东用户可能需要：① Paddle 作为替代 ② 本地支付网关（GrabPay、GoPay）③ 加密货币支付 |
| B-2 | **无公司主体** — 个人运营 SaaS 有法律和税务风险 | 🟡 中 | — | 无法合规收款 | 新加坡注册公司（最低成本 ~$300/年），Stripe 要求公司主体 |
| B-3 | **各国 AI 监管政策** — 欧盟 AI Act、中国 AI 备案等 | 🟡 中 | 中 | 某些市场无法进入 | 先做监管友好的市场（东南亚、中东）；避开监管严格的市场（中国大陆、欧盟）直到合规 |
| B-4 | **竞品先发优势** — MaxClaw/KimClaw 已有用户基础 | 🟡 中 | 高 | 获客困难 | 差异化：① 多模型支持（竞品锁定单一模型）② 更低价格 ③ 瞄准竞品未覆盖的地区 |
| B-5 | **用户增长与资源成本不匹配** — 每用户需要独立容器，成本线性增长 | 🔴 高 | 中 | 越多用户越亏 | 精算单用户成本（容器 + 模型 API）；确保订阅定价覆盖成本 + 毛利；Free 用户限时体验（如 7 天） |

---

### 14.7 风险优先级矩阵

按 **严重度 × 概率** 排序，MVP 上线前必须解决的 TOP 5：

| 优先级 | 风险编号 | 风险 | 必须在何时解决 |
|--------|----------|------|---------------|
| ~~**P0**~~ | ~~E-5~~ | ~~OpenClaw License 确认~~ ✅ **已解决 — MIT License，可商用** | ~~**立即**~~ Done |
| ~~**P0**~~ | ~~I-3~~ | ~~数据库备份~~ ✅ **已解决 — pg_dump 每 6h → OSS + 一键恢复** | ~~**Week 1**~~ Done |
| ~~**P0**~~ | ~~D-1~~ | ~~积分扣费竞态条件~~ ✅ **已解决 — SELECT FOR UPDATE 行锁** | ~~**Week 2**~~ Done |
| ~~**P0**~~ | ~~D-2~~ | ~~Usage callback 丢失兜底~~ ✅ **已解决 — 双通道 Redis 去重扣费** | ~~**Week 3**~~ Done |
| **P1** | C-1 | 单机容器密度上限 | **上线后** — 清楚知道天花板在哪，提前规划扩容节点 |

---

## 15. 产品设计原则 — 10 岁小孩也能用

> **核心理念**：Clawzy 的竞争力不在技术多牛，而在用户用起来多简单。一个 10 岁小孩不看说明书也能从下载到聊天。技术复杂度全部藏在后端，用户只看到一个"会说话的龙虾"。

---

### 15.1 极简用户链路

```
下载 App → 手机号/邮箱注册 → 龙虾自动上线 → 直接开聊
```

- **零配置**：注册完自动创建 Agent、自动分配默认模型、自动启动容器，用户不需要知道这些事情在发生
- **零等待感**：容器在后台创建，前端用动画过渡（龙虾"正在醒来..."），让等待变成体验的一部分
- **零术语**：用户界面不出现 "模型"、"Token"、"API"、"容器" 这些词

### 15.2 用户语言映射表

技术概念不能暴露给用户，全部翻译成自然语言：

| 技术概念 | 用户看到的 | 示例 |
|----------|-----------|------|
| AI Model | 龙虾的大脑 | "给龙虾换个更聪明的大脑" |
| Token | — (不暴露) | — |
| Credits / 积分 | 能量 ⚡ | "你还剩 3000 能量" |
| Agent 状态 running | 🟢 在线 | "你的龙虾正在等你" |
| Agent 状态 stopped | 😴 休息中 | "龙虾睡着了，点击唤醒" |
| Agent 状态 error | 🤒 不舒服 | "龙虾不太舒服，我们正在治疗" |
| 切换模型 | 换个大脑 | 滑动选择，标注"更聪明/更快/更省能量" |
| 订阅套餐 | 龙虾套餐 | "小龙虾 / 大龙虾 / 超级龙虾" |
| Conversation | 对话 | "你和龙虾的第 12 次对话" |
| Skill / Plugin | 技能 | "教龙虾新技能" |

### 15.3 交互设计红线

以下情况 **绝对不允许** 出现在用户界面：

| ❌ 禁止 | ✅ 替代方案 |
|---------|------------|
| 展示报错堆栈 / error code | 友好插画 + "龙虾遇到了点问题，正在修复" |
| 让用户填 API Key | 平台统一代理，用户永远不碰 API Key |
| 让用户选 JSON 配置 | 可视化开关 / 滑块 / 卡片选择 |
| 空白页面 / 无内容状态 | 引导卡片："试试对龙虾说'你好'" |
| 加载超过 3 秒无反馈 | 骨架屏 + 龙虾动画 + 文案（"龙虾正在思考..."） |
| 需要阅读文档才能使用 | 首次使用引导气泡（最多 3 步） |
| 英文界面（目标用户非英语） | 自动检测语言，支持中/英/日/韩/阿拉伯等 |

### 15.4 模型选择简化

用户不需要知道什么是 "DeepSeek V3" 或 "Claude Sonnet"，只需要选择：

```
┌─────────────────────────────────────────────────┐
│  给龙虾选个大脑                                    │
│                                                   │
│  ⚡ 闪电快    → 回答快，省能量         [Qwen Turbo]  │
│  🧠 聪明      → 日常聊天最佳           [DeepSeek V3] │
│  🎓 超级聪明  → 复杂任务，写代码       [Claude/GPT-4o]│
│  💰 能量消耗: ⚡ < 🧠 < 🎓                          │
│                                                   │
│  不知道选哪个？推荐 🧠 聪明 ← 默认选中              │
└─────────────────────────────────────────────────┘
```

### 15.5 关键体验指标

| 指标 | 目标 | 衡量方式 |
|------|------|----------|
| 注册到第一次对话 | < 90 秒 | 从点击注册到收到龙虾第一条回复 |
| 首次使用引导步骤 | ≤ 3 步 | 注册 → (自动创建) → 开聊 |
| 首次使用放弃率 | < 15% | 注册后 5 分钟内未发送第一条消息 |
| 用户需要看帮助文档的比例 | < 5% | 如果超过 5%，说明界面不够直觉 |
| 任何操作的点击次数 | ≤ 3 次 | 从当前页面到完成任何操作 |
