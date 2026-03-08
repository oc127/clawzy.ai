"""管理后台 API — 系统健康、指标、手动干预。

用 API Key 鉴权（运维专用，不走 JWT）。
"""

import json
import logging
import re

from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.circuit_breaker import circuit_breaker
from app.core.metrics import get_all_metrics
from app.core.redis import get_redis
from app.core.docker_manager import docker_manager
from app.deps import get_db
from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.services.health_service import run_all_health_checks, HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


async def verify_admin_key(x_admin_key: str = Header(...)):
    """简单 API Key 鉴权。"""
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")


@router.get("/health", dependencies=[Depends(verify_admin_key)])
async def system_health():
    """深度健康检查：DB + Redis + LiteLLM。"""
    results = await run_all_health_checks()
    overall = "healthy"
    for r in results:
        if r.status == HealthStatus.UNHEALTHY:
            overall = "unhealthy"
            break
        elif r.status == HealthStatus.DEGRADED:
            overall = "degraded"

    return {
        "overall": overall,
        "services": [
            {
                "service": r.service,
                "status": r.status.value,
                "latency_ms": round(r.latency_ms, 1),
                "details": r.details,
            }
            for r in results
        ],
    }


@router.get("/metrics", dependencies=[Depends(verify_admin_key)])
async def system_metrics():
    """所有采集的指标。"""
    return await get_all_metrics()


@router.get("/models/status", dependencies=[Depends(verify_admin_key)])
async def model_status():
    """所有模型的熔断器状态。"""
    from app.core.model_fallback import MODEL_FALLBACK_CHAIN
    models = list(MODEL_FALLBACK_CHAIN.keys())
    statuses = []
    for model in models:
        status_data = await circuit_breaker.get_model_status(model)
        statuses.append(status_data)
    return {"models": statuses}


@router.post("/agents/{agent_id}/restart", dependencies=[Depends(verify_admin_key)])
async def restart_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """强制重启 Agent 容器。"""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent or not agent.container_id:
        raise HTTPException(status_code=404, detail="Agent or container not found")

    try:
        docker_manager.stop_container(agent.container_id)
        docker_manager.start_container(agent.container_id)
        agent.status = AgentStatus.running
        await db.commit()
        return {"status": "restarted", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", dependencies=[Depends(verify_admin_key)])
async def system_stats(db: AsyncSession = Depends(get_db)):
    """系统概览统计。"""
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    agent_count = (await db.execute(select(func.count()).select_from(Agent))).scalar_one()
    running_agents = (await db.execute(
        select(func.count()).where(Agent.status == AgentStatus.running)
    )).scalar_one()
    error_agents = (await db.execute(
        select(func.count()).where(Agent.status == AgentStatus.error)
    )).scalar_one()

    return {
        "users": user_count,
        "agents": {"total": agent_count, "running": running_agents, "error": error_agents},
    }


@router.get("/health/history", dependencies=[Depends(verify_admin_key)])
async def health_history():
    """最近一次 Celery 定时深度检查的结果。"""
    r = await get_redis()
    data = await r.get("clawzy:health:latest")
    if data:
        return {"results": json.loads(data)}
    return {"results": []}


@router.get("/metrics/prometheus", dependencies=[Depends(verify_admin_key)])
async def prometheus_metrics():
    """Prometheus text format 指标输出 — 供外部 Prometheus / Grafana 抓取。"""
    data = await get_all_metrics()
    lines: list[str] = []

    for name, val in data.get("counters", {}).items():
        safe = _sanitize_metric_name(name)
        lines.append(f"clawzy_counter_{safe} {val}")

    for name, val in data.get("gauges", {}).items():
        safe = _sanitize_metric_name(name)
        lines.append(f"clawzy_gauge_{safe} {val}")

    for name, lat in data.get("latencies", {}).items():
        safe = _sanitize_metric_name(name)
        for quantile in ("p50", "p95", "p99", "avg"):
            lines.append(f"clawzy_latency_{safe}_{quantile} {lat.get(quantile, 0)}")
        lines.append(f"clawzy_latency_{safe}_count {lat.get('count', 0)}")

    return PlainTextResponse("\n".join(lines) + "\n")


def _sanitize_metric_name(name: str) -> str:
    """将 Redis 指标名转换为 Prometheus 合法名（仅字母数字下划线）。"""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


@router.post("/deploy-event", dependencies=[Depends(verify_admin_key)])
async def record_deploy_event(event: dict):
    """记录部署/回滚事件到 Redis（最近 50 条）。"""
    r = await get_redis()
    key = "clawzy:deploy:history"
    await r.lpush(key, json.dumps(event))
    await r.ltrim(key, 0, 49)
    return {"status": "recorded"}


@router.get("/deploy-history", dependencies=[Depends(verify_admin_key)])
async def deploy_history():
    """最近 50 次部署/回滚事件。"""
    r = await get_redis()
    raw = await r.lrange("clawzy:deploy:history", 0, 49)
    events = []
    for item in raw:
        try:
            events.append(json.loads(item))
        except (json.JSONDecodeError, TypeError):
            continue
    return {"events": events}


@router.post("/ops/chat", dependencies=[Depends(verify_admin_key)])
async def ops_agent_chat(request: dict):
    """与运维 Agent 对话。发送消息，Agent 会自动调用工具分析和执行。"""
    from app.services.ops_chat_service import ops_chat
    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="message required")
    reply = await ops_chat(message)
    return {"reply": reply}
