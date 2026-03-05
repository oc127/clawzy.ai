# Clawzy.ai

AI assistant platform — each user gets an isolated AI agent powered by OpenClaw, with multi-model routing via LiteLLM.

## Architecture

```
Browser ─ WebSocket ─→ Nginx ─→ FastAPI ─→ OpenClaw Container (per user)
                                   │               │
                                   ├── PostgreSQL   └── LiteLLM Proxy
                                   ├── Redis             ├── DeepSeek
                                   └── Celery             ├── Qwen
                                                          └── (Claude, GPT-4o, ...)
```

- **Backend**: FastAPI (Python 3.12, async)
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS v4
- **Database**: PostgreSQL 16 (asyncpg) + Redis 7
- **Model Router**: LiteLLM (DeepSeek, Qwen, extensible)
- **Agent Runtime**: OpenClaw in isolated Docker containers
- **Task Queue**: Celery + Redis (health checks, billing)

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys (DEEPSEEK_API_KEY, DASHSCOPE_API_KEY, etc.)

# 2. Start all services
docker compose up -d

# 3. Verify
curl http://localhost:8000/health        # Backend
curl http://localhost:4000/health        # LiteLLM
open http://localhost:3000               # Frontend
```

### With Nginx (full stack)

```bash
docker compose --profile proxy up -d
```

## Development

```bash
# Backend only (hot reload)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend only (hot reload)
cd web && npm install && npm run dev

# Run tests
cd backend && pytest

# Database migrations
cd backend && alembic upgrade head
```

## Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

See [DEPLOY.md](DEPLOY.md) for full deployment guide (Alibaba Cloud ECS).

## Project Structure

```
backend/          FastAPI API + services + models
web/              Next.js frontend
litellm/          LiteLLM model routing config
openclaw/         OpenClaw agent config
nginx/            Reverse proxy config
scripts/          Setup, deploy, backup scripts
```

## Key Features

- Multi-language UI (zh/en/ja/ko)
- Real-time streaming chat via WebSocket
- Per-user isolated agent containers
- Credit-based billing with Stripe
- Auto-healing with circuit breakers
- Telegram ops bot for alerts

## Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) — Full system design (51KB)
- [DEPLOY.md](DEPLOY.md) — Deployment guide
