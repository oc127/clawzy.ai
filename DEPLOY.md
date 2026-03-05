# Clawzy.ai — 部署指南

> 目标：阿里云新加坡 ECS (4C8G Ubuntu 22.04)
> 架构：Nginx + Next.js + FastAPI + OpenClaw + LiteLLM + PostgreSQL + Redis
> 模型：DeepSeek (V3 Chat / R1 Reasoner) + Qwen (Max / Plus / Turbo)

---

## 架构图

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │   Nginx :80/443│  ← SSL termination
              └───────┬────────┘
           ┌──────────┼──────────┐
           ▼          ▼          ▼
     ┌──────────┐ ┌────────┐ ┌────────────┐
     │ Next.js  │ │FastAPI │ │ WebSocket  │
     │ :3000    │ │ :8000  │ │ /ws/chat/* │
     └──────────┘ └───┬────┘ └─────┬──────┘
                      │            │
              ┌───────┴────┐  ┌────▼──────────┐
              │ PostgreSQL │  │ OpenClaw      │
              │ :5432      │  │ Containers    │
              ├────────────┤  │ (per user)    │
              │ Redis      │  └────┬──────────┘
              │ :6379      │       │
              └────────────┘  ┌────▼──────────┐
                              │ LiteLLM Proxy │
                              │ :4000         │
                              │ ├─ DeepSeek   │
                              │ ├─ Qwen       │
                              │ └─ (扩展...)   │
                              └───────────────┘
```

---

## Step 0: 准备工作

| 项目 | 获取方式 |
|------|----------|
| 阿里云 ECS 实例 | 控制台创建，选新加坡区，4C8G，Ubuntu 22.04 |
| SSH 密钥/密码 | 创建 ECS 时设置 |
| 域名 (clawzy.ai) | DNS A 记录指向 ECS 公网 IP |
| SSL 证书 | Let's Encrypt 或 Cloudflare Origin Certificate |
| DeepSeek API Key | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| DashScope API Key (Qwen) | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| Stripe 账号 (可选) | 用于付费订阅功能 |

---

## Step 1: SSH 登录服务器

```bash
ssh root@<YOUR_ECS_IP>

# 创建非 root 用户（推荐）
adduser clawzy
usermod -aG sudo clawzy
su - clawzy
```

---

## Step 2: 一键初始化

```bash
# 克隆项目
cd /opt
sudo mkdir -p clawzy && sudo chown $USER:$USER clawzy
git clone <YOUR_REPO_URL> clawzy
cd clawzy

# 运行初始化脚本（安装 Docker、防火墙、生成密钥）
bash scripts/setup-server.sh
```

这个脚本会自动：
- 安装 Docker + Docker Compose
- 配置 UFW 防火墙（只开 22/80/443）
- 从 `.env.example` 生成 `.env` 并自动生成随机密钥
- 拉取镜像并启动所有服务
- 配置数据库备份 cron（每 6 小时）

---

## Step 3: 填写 API Key

```bash
nano /opt/clawzy/.env
```

**必填**：
```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
JWT_SECRET=<openssl rand -hex 32 的输出>
```

**可选（付费功能）**：
```env
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_STARTER=price_xxx
STRIPE_PRICE_PRO=price_xxx
STRIPE_PRICE_BUSINESS=price_xxx
```

**可选（邮件）**：
```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_xxx
SMTP_FROM_EMAIL=noreply@clawzy.ai
```

修改后重启：
```bash
docker compose -f docker-compose.prod.yml restart
```

---

## Step 4: 配置 SSL 证书

### 方案 A: Let's Encrypt (推荐)

```bash
# 安装 certbot
sudo apt install -y certbot

# 先临时停 Nginx
docker compose -f docker-compose.prod.yml stop nginx

# 生成证书
sudo certbot certonly --standalone -d clawzy.ai -d www.clawzy.ai

# 复制到 Nginx 期望的路径
sudo mkdir -p /etc/ssl/clawzy
sudo cp /etc/letsencrypt/live/clawzy.ai/fullchain.pem /etc/ssl/clawzy/cert.pem
sudo cp /etc/letsencrypt/live/clawzy.ai/privkey.pem /etc/ssl/clawzy/key.pem

# 重启 Nginx
docker compose -f docker-compose.prod.yml start nginx
```

自动续期：
```bash
# 添加 cron
echo "0 3 * * * certbot renew --pre-hook 'docker compose -f /opt/clawzy/docker-compose.prod.yml stop nginx' --post-hook 'cp /etc/letsencrypt/live/clawzy.ai/fullchain.pem /etc/ssl/clawzy/cert.pem && cp /etc/letsencrypt/live/clawzy.ai/privkey.pem /etc/ssl/clawzy/key.pem && docker compose -f /opt/clawzy/docker-compose.prod.yml start nginx'" | sudo tee -a /etc/crontab
```

### 方案 B: Cloudflare Origin Certificate

1. Cloudflare Dashboard → SSL/TLS → Origin Server → Create Certificate
2. 下载 cert.pem 和 key.pem 到 `/etc/ssl/clawzy/`
3. Cloudflare SSL 模式设为 `Full (strict)`

---

## Step 5: 配置 Nginx SSL 挂载

生产环境的 Nginx 需要挂载 SSL 证书目录。编辑 `docker-compose.prod.yml`，给 nginx 服务添加证书卷：

```yaml
  nginx:
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/ssl/clawzy:/etc/ssl/clawzy:ro    # ← 添加这行
```

---

## Step 6: 运行数据库迁移

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## Step 7: 验证部署

```bash
# 一键验证
bash scripts/smoke-test.sh

# 或者手动检查
curl http://127.0.0.1:8000/health              # Backend
curl http://127.0.0.1:4000/health/liveliness    # LiteLLM
curl http://127.0.0.1:3000                      # Frontend
curl -k https://clawzy.ai/health                # 通过 Nginx

# 检查所有容器状态
docker compose -f docker-compose.prod.yml ps
```

### 验证模型可用

```bash
source .env
curl -s http://127.0.0.1:4000/v1/models \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" | jq '.data[].id'
```

期望输出：
```
"deepseek-chat"
"deepseek-reasoner"
"qwen-max"
"qwen-plus"
"qwen-turbo"
```

---

## 后续部署（更新代码）

```bash
cd /opt/clawzy
bash scripts/deploy.sh
```

这个脚本会自动：拉代码 → 构建镜像 → 启动服务 → 运行迁移 → 冒烟测试

跳过构建或迁移：
```bash
bash scripts/deploy.sh --skip-build
bash scripts/deploy.sh --skip-migrate
```

---

## 常用运维命令

```bash
# 查看日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f litellm

# 重启单个服务
docker compose -f docker-compose.prod.yml restart backend

# 数据库备份（手动）
bash scripts/backup-db.sh

# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 停止并清除数据（⚠️ 慎用）
docker compose -f docker-compose.prod.yml down -v
```

---

## 安全备忘

- `.env` 权限 `600`，只有 owner 可读写
- 所有内部端口绑定 `127.0.0.1`，只有 Nginx 暴露 80/443
- UFW 只开 SSH (22) / HTTP (80) / HTTPS (443)
- `LITELLM_SALT_KEY` 一旦设定**不可更改**
- 每 6 小时自动备份 PostgreSQL（setup-server.sh 已配置）
- Stripe Webhook 通过签名验证，不需要额外鉴权

---

## 文件结构

```
clawzy.ai/
├── docker-compose.yml          # 开发环境编排
├── docker-compose.prod.yml     # 生产环境编排
├── .env.example                # 环境变量模板
├── .env                        # 实际配置（不入 git）
├── backend/                    # FastAPI 后端
├── web/                        # Next.js 前端
├── nginx/                      # Nginx 反向代理配置
│   ├── nginx.conf
│   └── conf.d/clawzy.conf
├── litellm/
│   └── config.yaml             # LiteLLM 模型路由配置
├── openclaw/
│   └── openclaw.json           # OpenClaw 模型配置
└── scripts/
    ├── setup-server.sh         # 一键服务器初始化
    ├── deploy.sh               # 生产部署脚本
    ├── smoke-test.sh           # 部署验证测试
    └── backup-db.sh            # 数据库备份
```
