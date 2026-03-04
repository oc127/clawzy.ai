"""轻量指标收集 — Redis-based，无需 Prometheus。

指标类型：
- counter: 计数器（请求数、错误数）
- gauge: 当前值（活跃容器数）
- latency: 延迟分布（p50/p95/p99）

所有指标存 Redis，带 TTL 自动清理。
"""

import time
import logging

from app.core.redis import get_redis
from app.config import settings

logger = logging.getLogger(__name__)

PREFIX = "clawzy:metrics"


async def inc_counter(name: str, labels: dict[str, str] | None = None, amount: int = 1) -> None:
    """递增计数器。"""
    r = await get_redis()
    label_str = _labels_to_str(labels)
    key = f"{PREFIX}:counter:{name}{label_str}"
    await r.incrby(key, amount)
    await r.expire(key, settings.metrics_retention_hours * 3600)


async def record_latency(name: str, latency_ms: float, labels: dict[str, str] | None = None) -> None:
    """记录延迟值到 sorted set（用于算分位数）。"""
    r = await get_redis()
    label_str = _labels_to_str(labels)
    key = f"{PREFIX}:latency:{name}{label_str}"
    now = time.time()
    await r.zadd(key, {f"{latency_ms}:{now}": now})
    cutoff = now - (settings.metrics_retention_hours * 3600)
    await r.zremrangebyscore(key, 0, cutoff)
    await r.expire(key, settings.metrics_retention_hours * 3600 + 300)


async def set_gauge(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """设置 gauge 值。"""
    r = await get_redis()
    label_str = _labels_to_str(labels)
    key = f"{PREFIX}:gauge:{name}{label_str}"
    await r.set(key, str(value), ex=settings.metrics_retention_hours * 3600)


async def get_all_metrics() -> dict:
    """获取所有当前指标（给管理后台用）。"""
    r = await get_redis()
    result: dict = {"counters": {}, "gauges": {}, "latencies": {}}

    async for key in r.scan_iter(f"{PREFIX}:*"):
        key_str = key.decode() if isinstance(key, bytes) else key
        parts = key_str.replace(PREFIX + ":", "").split(":", 1)
        metric_type = parts[0]
        metric_name = parts[1] if len(parts) > 1 else "unknown"

        if metric_type == "counter":
            val = await r.get(key)
            result["counters"][metric_name] = int(val) if val else 0
        elif metric_type == "gauge":
            val = await r.get(key)
            result["gauges"][metric_name] = float(val) if val else 0
        elif metric_type == "latency":
            count = await r.zcard(key)
            if count > 0:
                members = await r.zrange(key, 0, -1)
                latencies = sorted([float(m.decode().split(":")[0]) for m in members])
                result["latencies"][metric_name] = {
                    "count": len(latencies),
                    "p50": latencies[len(latencies) // 2] if latencies else 0,
                    "p95": latencies[int(len(latencies) * 0.95)] if latencies else 0,
                    "p99": latencies[int(len(latencies) * 0.99)] if latencies else 0,
                    "avg": round(sum(latencies) / len(latencies), 1) if latencies else 0,
                }

    return result


def _labels_to_str(labels: dict[str, str] | None) -> str:
    if not labels:
        return ""
    sorted_labels = sorted(labels.items())
    return ":" + ",".join(f"{k}={v}" for k, v in sorted_labels)
