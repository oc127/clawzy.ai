"""运维工具注册表 — 每个工具 = 一个 function calling 定义 + 一个执行函数。"""

import json
import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Coroutine

import docker

from app.config import settings

logger = logging.getLogger(__name__)


class ToolPermission(str, Enum):
    READ = "read"
    WRITE = "write"


@dataclass
class OpsTool:
    name: str
    description: str
    parameters: dict
    permission: ToolPermission
    handler: Callable[..., Coroutine[Any, Any, str]]


OPS_TOOLS: dict[str, OpsTool] = {}


def register_tool(name: str, description: str, parameters: dict, permission: ToolPermission = ToolPermission.READ):
    def decorator(func: Callable[..., Coroutine[Any, Any, str]]):
        OPS_TOOLS[name] = OpsTool(
            name=name,
            description=description,
            parameters=parameters,
            permission=permission,
            handler=func,
        )
        return func
    return decorator


# ============================================================
#  READ tools
# ============================================================

@register_tool(
    name="check_health",
    description="检查所有基础设施服务的健康状态（数据库、Redis、LiteLLM、磁盘、Docker、Celery）",
    parameters={"type": "object", "properties": {}, "required": []},
)
async def check_health() -> str:
    from app.services.health_service import run_all_health_checks
    results = await run_all_health_checks()
    lines = []
    for r in results:
        icon = {"healthy": "OK", "degraded": "WARN", "unhealthy": "FAIL"}.get(r.status.value, "?")
        lines.append(f"[{icon}] {r.service}: {r.status.value} ({r.latency_ms:.0f}ms) {r.details}")
    return "\n".join(lines)


@register_tool(
    name="get_metrics",
    description="获取系统指标：请求数、错误率、延迟分位数、活跃容器数",
    parameters={"type": "object", "properties": {}, "required": []},
)
async def get_metrics() -> str:
    from app.core.metrics import get_all_metrics
    metrics = await get_all_metrics()
    return json.dumps(metrics, indent=2, ensure_ascii=False)


@register_tool(
    name="get_logs",
    description="获取指定服务的最近日志",
    parameters={
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "enum": ["backend", "litellm", "postgres", "redis", "celery-worker", "celery-beat"],
            },
            "lines": {"type": "integer", "default": 50},
        },
        "required": ["service"],
    },
)
async def get_logs(service: str, lines: int = 50) -> str:
    try:
        client = docker.from_env()
        container = client.containers.get(f"clawzy-{service}")
        log_output = container.logs(tail=min(lines, 200)).decode("utf-8", errors="replace")
        return log_output[-4000:]
    except Exception as e:
        return f"Error fetching logs: {e}"


@register_tool(
    name="list_containers",
    description="列出所有 Clawzy 相关容器及其状态",
    parameters={"type": "object", "properties": {}, "required": []},
)
async def list_containers() -> str:
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True, filters={"name": "clawzy"})
        lines = []
        for c in containers:
            tags = c.image.tags[0] if c.image.tags else "unknown"
            lines.append(f"{c.name}: {c.status} (image: {tags})")
        return "\n".join(lines) if lines else "No clawzy containers found"
    except Exception as e:
        return f"Error: {e}"


@register_tool(
    name="check_circuit_breakers",
    description="查看所有模型的熔断器状态",
    parameters={"type": "object", "properties": {}, "required": []},
)
async def check_circuit_breakers() -> str:
    from app.core.circuit_breaker import circuit_breaker
    from app.core.model_fallback import MODEL_FALLBACK_CHAIN
    results = []
    for model in MODEL_FALLBACK_CHAIN:
        status = await circuit_breaker.get_model_status(model)
        results.append(status)
    return json.dumps(results, indent=2, ensure_ascii=False)


@register_tool(
    name="run_smoke_test",
    description="对 LiteLLM 执行冒烟测试，验证模型是否能正常回复",
    parameters={"type": "object", "properties": {}, "required": []},
)
async def run_smoke_test() -> str:
    import httpx
    results = []
    models = ["deepseek-chat", "qwen-turbo"]
    for model in models:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{settings.litellm_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.litellm_master_key}"},
                    json={"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 10},
                )
                if resp.status_code == 200:
                    results.append(f"[OK] {model}: responding")
                else:
                    results.append(f"[FAIL] {model}: HTTP {resp.status_code}")
        except Exception as e:
            results.append(f"[FAIL] {model}: {e}")
    return "\n".join(results)


@register_tool(
    name="send_notification",
    description="发送通知给管理员",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "通知内容"},
            "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
        },
        "required": ["message"],
    },
)
async def send_notification(message: str, severity: str = "info") -> str:
    from app.core.alerting import send_alert
    success = await send_alert("Ops Agent", message, severity)
    return "Notification sent" if success else "Failed to send (check webhook config)"


# ============================================================
#  WRITE tools (require approval notification)
# ============================================================

@register_tool(
    name="restart_service",
    description="重启指定的 Docker 容器服务",
    parameters={
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "enum": ["backend", "litellm", "redis", "celery-worker", "celery-beat"],
            },
        },
        "required": ["service"],
    },
    permission=ToolPermission.WRITE,
)
async def restart_service(service: str) -> str:
    if service == "postgres":
        return "Refused: cannot restart database via agent"
    try:
        client = docker.from_env()
        container = client.containers.get(f"clawzy-{service}")
        container.restart(timeout=30)
        return f"{service} restarted, status: {container.status}"
    except Exception as e:
        return f"Restart failed: {e}"


@register_tool(
    name="run_backup",
    description="立即执行一次数据库备份",
    parameters={"type": "object", "properties": {}, "required": []},
    permission=ToolPermission.WRITE,
)
async def run_backup() -> str:
    try:
        result = subprocess.run(
            ["bash", "/opt/clawzy/scripts/backup-db.sh"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return f"Backup successful:\n{result.stdout[-500:]}"
        return f"Backup failed:\n{result.stderr[-500:]}"
    except Exception as e:
        return f"Backup error: {e}"


@register_tool(
    name="cleanup_containers",
    description="清理所有已停止的 Clawzy Agent 僵尸容器",
    parameters={"type": "object", "properties": {}, "required": []},
    permission=ToolPermission.WRITE,
)
async def cleanup_containers() -> str:
    try:
        client = docker.from_env()
        removed = client.containers.prune(filters={"label": "clawzy.managed=true"})
        count = len(removed.get("ContainersDeleted") or [])
        space = (removed.get("SpaceReclaimed") or 0) // 1024 // 1024
        return f"Cleaned {count} containers, freed {space}MB"
    except Exception as e:
        return f"Cleanup failed: {e}"


def get_tools_for_function_calling() -> list[dict]:
    """Generate OpenAI-compatible function calling tool definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in OPS_TOOLS.values()
    ]
