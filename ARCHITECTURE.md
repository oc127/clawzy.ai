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

### 7.4 Usage Callback

LiteLLM 支持自定义 callback，在每次请求完成后回调后端记录用量：

```yaml
# litellm/config.yaml 添加
litellm_settings:
  success_callback: ["custom_callback_api"]
  custom_callback_api_url: "http://clawzy-backend:8000/internal/usage-callback"
```

后端 `/internal/usage-callback` 接收用量数据后执行积分扣费。

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

## 14. 关键风险 & 应对

| 风险 | 影响 | 应对 |
|------|------|------|
| OpenClaw 上游 breaking change | Agent 挂掉 | 锁定镜像版本，手动测试后再升级 |
| 单机容器过多 OOM | 全部 Agent 崩溃 | 每容器 512MB 限制 + 监控报警 |
| 模型 API 涨价 | 毛利压缩 | Credits 换算表可随时调整 |
| Docker socket 安全风险 | 容器逃逸 | 生产用 Docker API over TCP + TLS |
| Stripe 合规 | 收款受限 | 新加坡公司注册，合规运营 |
