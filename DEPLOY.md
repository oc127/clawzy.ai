# Clawzy.ai — PoC 部署指南

> 目标：阿里云新加坡 ECS (4C8G Ubuntu 22.04)
> 架构：OpenClaw + LiteLLM Proxy + PostgreSQL，Docker Compose 编排
> 模型：DeepSeek (V3 Chat / R1 Reasoner) + Qwen (Max / Plus / Turbo)

---

## 架构图

```
┌─────────────────────────────────────────────────┐
│               Alibaba Cloud ECS                 │
│               4C8G Singapore                    │
│                                                 │
│  ┌───────────────┐     ┌─────────────────────┐  │
│  │  OpenClaw GW  │────▶│   LiteLLM Proxy     │  │
│  │  :18789/18790 │     │   :4000             │  │
│  └───────────────┘     │                     │  │
│                        │  ┌───────┐ ┌──────┐ │  │
│                        │  │DeepSk │ │ Qwen │ │  │
│                        │  │ API   │ │DashSc│ │  │
│                        │  └───────┘ └──────┘ │  │
│                        └──────────┬──────────┘  │
│                                   │             │
│                        ┌──────────▼──────────┐  │
│                        │   PostgreSQL 16     │  │
│                        │   :5432             │  │
│                        └─────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Step 0: 准备工作

在开始之前，确保你有：

| 项目 | 获取方式 |
|------|----------|
| 阿里云 ECS 实例 | 控制台创建，选新加坡区，4C8G，Ubuntu 22.04 |
| SSH 密钥/密码 | 创建 ECS 时设置 |
| DeepSeek API Key | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| DashScope API Key (Qwen) | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |

---

## Step 1: SSH 登录服务器

```bash
# 替换为你的 ECS 公网 IP
ssh root@<YOUR_ECS_IP>

# 如果用密钥文件
ssh -i ~/.ssh/your-key.pem root@<YOUR_ECS_IP>
```

首次登录建议：
```bash
# 创建非 root 用户（推荐）
adduser clawzy
usermod -aG sudo clawzy
su - clawzy
```

---

## Step 2: 安装 Docker

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装依赖
sudo apt-get install -y ca-certificates curl gnupg lsb-release git jq

# 添加 Docker 官方 GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
newgrp docker

# 验证
docker --version
docker compose version
```

> **国内镜像加速**：如果从新加坡拉 Docker Hub 慢，可配置阿里云镜像加速器：
> ```bash
> sudo mkdir -p /etc/docker
> sudo tee /etc/docker/daemon.json <<EOF
> {
>   "registry-mirrors": ["https://<your-id>.mirror.aliyuncs.com"]
> }
> EOF
> sudo systemctl restart docker
> ```

---

## Step 3: 克隆项目 & 配置

```bash
# 克隆项目
cd /opt
sudo mkdir -p clawzy && sudo chown $USER:$USER clawzy
git clone <YOUR_REPO_URL> clawzy
cd clawzy

# 从模板创建 .env
cp .env.example .env
chmod 600 .env
```

编辑 `.env`，填入你的 API Key：
```bash
nano .env
```

需要修改的关键项：
```env
# 自动生成 or 手动设置安全的密码
POSTGRES_PASSWORD=<生成一个强密码>
LITELLM_MASTER_KEY=sk-clawzy-<随机字符串>
LITELLM_SALT_KEY=salt-<随机字符串>

# ⬇️ 这两个必须填你自己的 API Key
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# OpenClaw gateway token
OPENCLAW_GATEWAY_TOKEN=<随机字符串>
```

快速生成随机密钥：
```bash
# 生成各项密钥
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)"
echo "LITELLM_MASTER_KEY=sk-clawzy-$(openssl rand -hex 16)"
echo "LITELLM_SALT_KEY=salt-$(openssl rand -hex 16)"
echo "OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 32)"
```

---

## Step 4: 配置防火墙

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP（后续 Nginx）
sudo ufw allow 443/tcp    # HTTPS（后续 Nginx）
sudo ufw enable
```

> LiteLLM (:4000) 和 OpenClaw (:18789/:18790) 都绑定在 127.0.0.1，不会暴露到公网。

---

## Step 5: 启动服务

```bash
cd /opt/clawzy

# 拉取镜像
docker compose pull

# 启动所有服务（后台运行）
docker compose up -d

# 查看日志
docker compose logs -f

# 查看运行状态
docker compose ps
```

启动顺序：PostgreSQL → LiteLLM (等 PG healthy) → OpenClaw (等 LiteLLM healthy)

---

## Step 6: 验证部署

### 6.1 检查服务状态

```bash
# 所有容器应该是 Up (healthy)
docker compose ps

# 检查 LiteLLM 健康
curl http://127.0.0.1:4000/health/liveliness
# 期望: {"status":"healthy"}
```

### 6.2 查看可用模型

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

### 6.3 测试 DeepSeek 模型

```bash
curl -s http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
    "max_tokens": 100
  }' | jq '.choices[0].message.content'
```

### 6.4 测试 Qwen 模型

```bash
curl -s http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-turbo",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
    "max_tokens": 100
  }' | jq '.choices[0].message.content'
```

### 6.5 一键 Smoke Test

```bash
bash scripts/smoke-test.sh
```

---

## Step 7: 使用 OpenClaw CLI（可选）

```bash
# 首次 onboard
docker compose run --rm openclaw-cli onboard

# 启动 CLI 交互
docker compose --profile cli run --rm openclaw-cli
```

---

## 常用运维命令

```bash
# 查看日志
docker compose logs -f litellm          # LiteLLM 日志
docker compose logs -f openclaw-gateway  # OpenClaw 日志
docker compose logs -f postgres          # PostgreSQL 日志

# 重启单个服务
docker compose restart litellm

# 更新镜像并重启
docker compose pull && docker compose up -d

# 停止所有服务
docker compose down

# 停止并清除数据（慎用）
docker compose down -v
```

---

## 安全备忘

- `.env` 文件权限设为 `600`，只有 owner 可读写
- 所有内部服务端口绑定 `127.0.0.1`，不暴露到公网
- 后续加 Nginx 反向代理 + Let's Encrypt SSL
- 定期备份 PostgreSQL 数据
- LiteLLM `LITELLM_SALT_KEY` 一旦设定不可更改

---

## 文件结构

```
clawzy.ai/
├── docker-compose.yml          # 服务编排
├── .env.example                # 环境变量模板
├── .env                        # 实际配置（不入 git）
├── .gitignore
├── DEPLOY.md                   # 本文档
├── litellm/
│   └── config.yaml             # LiteLLM 模型路由配置
├── openclaw/
│   └── openclaw.json           # OpenClaw 模型提供者配置
└── scripts/
    ├── setup-server.sh         # 一键服务器初始化
    └── smoke-test.sh           # 部署验证测试
```
