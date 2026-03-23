# Phase 1 部署指令 — 给 Claude Code

把下面的内容复制粘贴到 Claude Code 里，它会帮你完成全部操作。

---

## 第一步：先确认 SSH 能连上

在你 Mac 的终端里先试：

```bash
ssh root@8.216.45.216
```

如果忘记密码，去阿里云控制台（ecs.console.aliyun.com）→ 找到这台实例 → 更多 → 密码/密钥 → 重置实例密码。重置后需要重启实例。

---

## 第二步：打开 Claude Code，粘贴这段话

```
我需要你 SSH 到我的阿里云 ECS 服务器 8.216.45.216，帮我从零部署 Clawzy.ai 的 Phase 1。

服务器是空的 Ubuntu 22.04，什么都没装。请按以下顺序操作：

1. SSH 到 root@8.216.45.216

2. 安装 Docker 和 Docker Compose：
   - apt update && apt upgrade -y
   - 安装 Docker 官方版本（不要用 snap）
   - 确认 docker --version 和 docker compose version 能跑

3. 克隆项目：
   - git clone https://github.com/oc127/clawzy.ai.git /opt/clawzy
   - cd /opt/clawzy

4. 创建 .env 文件（从 .env.example 复制），自动生成安全密钥：
   - POSTGRES_PASSWORD: 随机生成
   - LITELLM_MASTER_KEY: sk-clawzy-随机
   - LITELLM_SALT_KEY: salt-随机
   - OPENCLAW_GATEWAY_TOKEN: 随机
   - DEEPSEEK_API_KEY 和 DASHSCOPE_API_KEY 先留空，等我填

5. 配置防火墙 UFW（只开 22/80/443）

6. 运行 docker compose pull && docker compose up -d

7. 等服务启动后，运行健康检查：
   - curl http://127.0.0.1:4000/health/liveliness
   - docker compose ps

8. 显示 .env 文件路径，提醒我填写 API Key

每一步都告诉我结果。如果有错误，帮我排查修复。
```

---

## 第三步：填写 API Key

部署完成后，Claude Code 会提醒你填写两个 API Key：

1. **DeepSeek API Key**
   - 去 https://platform.deepseek.com/api_keys 注册并创建

2. **DashScope API Key**（通义千问 Qwen）
   - 去 https://dashscope.console.aliyun.com/ 用阿里云账号开通

拿到后让 Claude Code 帮你填进 /opt/clawzy/.env，然后：

```
请帮我把 DEEPSEEK_API_KEY 和 DASHSCOPE_API_KEY 填入 /opt/clawzy/.env，然后重启服务并测试一次对话：

DEEPSEEK_API_KEY=你的key
DASHSCOPE_API_KEY=你的key

重启后测试：
curl http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"你好"}],"max_tokens":100}'
```

---

## 成功标志

当你看到 DeepSeek 或 Qwen 返回了一句中文回复，Phase 1 就完成了！
龙虾有脑子了，接下来就是 Phase 2：写后端 API。
