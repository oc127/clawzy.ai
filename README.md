# Nippon Claw

> Your AI Lobster, Any Brain.
>
> OpenClaw-as-a-Service — 为每位用户提供独立的 AI Agent 实例，支持多模型路由、Credits 计费和 ClawHub 技能市场。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 14 (App Router) · TypeScript · Tailwind CSS · shadcn/ui |
| 后端 | FastAPI · SQLAlchemy 2.0 (async) · asyncpg |
| 数据库 | PostgreSQL 16 |
| 模型路由 | LiteLLM Proxy |
| AI 引擎 | OpenClaw (Docker) |
| 支付 | Stripe |
| 反向代理 | Nginx |

---

## 快速启动（本地开发）

### 1. 克隆项目

```bash
git clone https://github.com/your-org/nipponclaw.git
cd nipponclaw
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入以下必填项：

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | 自定义 |
| `LITELLM_MASTER_KEY` | LiteLLM 管理密钥 | `openssl rand -hex 16` |
| `LITELLM_SALT_KEY` | LiteLLM 加密 Salt | `openssl rand -hex 16` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| `DASHSCOPE_API_KEY` | Qwen (DashScope) API Key | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| `JWT_SECRET` | JWT 签名密钥 | `openssl rand -hex 32` |
| `OPENCLAW_GATEWAY_TOKEN` | OpenClaw 网关 Token | `openssl rand -hex 32` |

### 3. 启动服务

```bash
docker compose up -d
```

首次启动需要拉取镜像，约 2–3 分钟。

### 4. 验证

```bash
# 后端健康检查
curl http://localhost/health

# 打开前端
open http://localhost
```

---

## 目录结构

```
nipponclaw/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # 路由 (auth, agents, chat, billing, skills, models)
│   │   ├── models/   # SQLAlchemy ORM
│   │   ├── schemas/  # Pydantic 请求/响应
│   │   ├── services/ # 业务逻辑
│   │   └── core/     # 基础设施 (database, security, rate_limit, docker_manager)
│   └── tests/
├── web/              # Next.js 前端
├── litellm/          # LiteLLM 模型路由配置
├── nginx/            # Nginx 反向代理
├── openclaw/         # OpenClaw 配置模板
└── scripts/          # 运维脚本
```

---

## 生产部署

详见 [DEPLOY.md](./DEPLOY.md)。

关键步骤：

1. 将域名 DNS 指向 ECS 公网 IP
2. 在 `.env` 中设置 `DEPLOY_ENV=production`，并配置所有密钥
3. 配置 HTTPS（Cloudflare 代理或 Let's Encrypt）
4. `docker compose up -d`
5. 运行冒烟测试：`bash scripts/smoke-test.sh`

---

## API 文档

开发环境下访问：

- Swagger UI：[http://localhost/docs](http://localhost/docs)
- ReDoc：[http://localhost/redoc](http://localhost/redoc)

---

## 许可证

Private — All rights reserved.
