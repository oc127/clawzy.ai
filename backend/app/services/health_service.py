"""深度健康探针 — 真正测试服务是否能响应，不只是看容器状态。

检测项：
1. PostgreSQL: 实际执行 SELECT 1
2. Redis: PING + 内存用量
3. LiteLLM: 健康端点 + 模型列表
4. Agent 容器: HTTP 健康检查
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

import httpx
from sqlalchemy import text

from app.config import settings
from app.core.database import async_session
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    service: str
    status: HealthStatus
    latency_ms: float
    details: str = ""
    checked_at: float = field(default_factory=time.time)


async def check_database() -> HealthCheckResult:
    """深度 DB 探针：执行真实查询，测量延迟。"""
    start = time.time()
    try:
        async with async_session() as db:
            result = await db.execute(text("SELECT 1"))
            result.scalar_one()
            latency = (time.time() - start) * 1000

            if latency > 1000:
                return HealthCheckResult("database", HealthStatus.DEGRADED, latency, "Slow (>1s)")
            return HealthCheckResult("database", HealthStatus.HEALTHY, latency)
    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheckResult("database", HealthStatus.UNHEALTHY, latency, str(e))


async def check_redis() -> HealthCheckResult:
    """深度 Redis 探针：PING + 内存检查。"""
    start = time.time()
    try:
        r = await get_redis()
        await r.ping()
        info = await r.info("memory")
        latency = (time.time() - start) * 1000
        used_mb = info.get("used_memory", 0) / (1024 * 1024)

        if used_mb > 400:
            return HealthCheckResult("redis", HealthStatus.DEGRADED, latency, f"High memory: {used_mb:.0f}MB")
        return HealthCheckResult("redis", HealthStatus.HEALTHY, latency, f"Memory: {used_mb:.0f}MB")
    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheckResult("redis", HealthStatus.UNHEALTHY, latency, str(e))


async def check_litellm() -> HealthCheckResult:
    """深度 LiteLLM 探针：健康端点 + 模型列表。"""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.litellm_url}/health/liveliness")
            if resp.status_code != 200:
                latency = (time.time() - start) * 1000
                return HealthCheckResult("litellm", HealthStatus.UNHEALTHY, latency,
                                         f"Health endpoint returned {resp.status_code}")

            resp = await client.get(
                f"{settings.litellm_url}/v1/models",
                headers={"Authorization": f"Bearer {settings.litellm_master_key}"},
            )
            latency = (time.time() - start) * 1000
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                if not models:
                    return HealthCheckResult("litellm", HealthStatus.DEGRADED, latency, "No models available")
                return HealthCheckResult("litellm", HealthStatus.HEALTHY, latency, f"{len(models)} models")
            else:
                return HealthCheckResult("litellm", HealthStatus.DEGRADED, latency,
                                         f"Model list returned {resp.status_code}")
    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheckResult("litellm", HealthStatus.UNHEALTHY, latency, str(e))


async def check_agent_container(container_id: str, ws_port: int) -> HealthCheckResult:
    """深度容器探针：HTTP 健康检查。"""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://127.0.0.1:{ws_port}/health")
            latency = (time.time() - start) * 1000
            if resp.status_code == 200:
                return HealthCheckResult(f"agent:{container_id[:12]}", HealthStatus.HEALTHY, latency)
            else:
                return HealthCheckResult(f"agent:{container_id[:12]}", HealthStatus.DEGRADED, latency,
                                         f"HTTP {resp.status_code}")
    except httpx.ConnectError:
        latency = (time.time() - start) * 1000
        return HealthCheckResult(f"agent:{container_id[:12]}", HealthStatus.UNHEALTHY, latency, "Connection refused")
    except httpx.TimeoutException:
        latency = (time.time() - start) * 1000
        return HealthCheckResult(f"agent:{container_id[:12]}", HealthStatus.UNHEALTHY, latency, "Timeout")
    except Exception as e:
        latency = (time.time() - start) * 1000
        return HealthCheckResult(f"agent:{container_id[:12]}", HealthStatus.UNHEALTHY, latency, str(e))


async def run_all_health_checks() -> list[HealthCheckResult]:
    """并行跑所有基础设施健康检查。"""
    results = await asyncio.gather(
        check_database(),
        check_redis(),
        check_litellm(),
        return_exceptions=True,
    )

    clean_results = []
    for r in results:
        if isinstance(r, Exception):
            clean_results.append(HealthCheckResult("unknown", HealthStatus.UNHEALTHY, 0, str(r)))
        else:
            clean_results.append(r)

    return clean_results
