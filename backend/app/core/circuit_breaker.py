"""熔断器 — Redis-backed，多进程共享状态。

三个状态：
- CLOSED: 正常通行
- OPEN: 模型挂了，请求直接跳过（快速失败）
- HALF_OPEN: 试探恢复中，放一个请求过去测试

状态存在 Redis 里，所有 uvicorn worker + Celery worker 共享同一视图。
"""

import time
import logging
from enum import Enum
from dataclasses import dataclass

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5       # 多少次失败后打开熔断
    recovery_timeout: int = 60       # 多少秒后尝试半开探测
    success_threshold: int = 2       # 半开状态下几次成功才关闭
    window_seconds: int = 300        # 滑动窗口时长


class CircuitBreaker:
    """Per-model 熔断器，用 Redis sorted set 做滑动窗口计数。"""

    KEY_PREFIX = "clawzy:cb"

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self.config = config or CircuitBreakerConfig()

    def _key(self, model: str, suffix: str) -> str:
        return f"{self.KEY_PREFIX}:{model}:{suffix}"

    async def can_request(self, model: str) -> bool:
        """检查这个模型是否允许发请求。"""
        r = await get_redis()
        state = await self._get_state(r, model)

        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            opened_at = await r.get(self._key(model, "opened_at"))
            if opened_at and time.time() - float(opened_at) > self.config.recovery_timeout:
                await self._set_state(r, model, CircuitState.HALF_OPEN)
                return True
            return False
        elif state == CircuitState.HALF_OPEN:
            return True

        return True

    async def record_success(self, model: str) -> None:
        """记录成功请求。半开状态下连续成功 N 次后关闭熔断。"""
        r = await get_redis()
        state = await self._get_state(r, model)

        if state == CircuitState.HALF_OPEN:
            count = await r.incr(self._key(model, "half_open_successes"))
            if count >= self.config.success_threshold:
                await self._set_state(r, model, CircuitState.CLOSED)
                await r.delete(self._key(model, "half_open_successes"))
                logger.info("Circuit CLOSED for model %s (recovered)", model)

    async def record_failure(self, model: str) -> None:
        """记录失败请求。可能触发熔断。"""
        r = await get_redis()
        state = await self._get_state(r, model)
        now = time.time()

        if state == CircuitState.HALF_OPEN:
            await self._set_state(r, model, CircuitState.OPEN)
            await r.set(self._key(model, "opened_at"), str(now), ex=self.config.recovery_timeout * 3)
            logger.warning("Circuit re-OPENED for model %s (half-open probe failed)", model)
            return

        # 滑动窗口计数
        failures_key = self._key(model, "failures")
        await r.zadd(failures_key, {str(now): now})
        cutoff = now - self.config.window_seconds
        await r.zremrangebyscore(failures_key, 0, cutoff)
        await r.expire(failures_key, self.config.window_seconds + 60)

        failure_count = await r.zcard(failures_key)
        if failure_count >= self.config.failure_threshold:
            await self._set_state(r, model, CircuitState.OPEN)
            await r.set(self._key(model, "opened_at"), str(now), ex=self.config.recovery_timeout * 3)
            logger.warning(
                "Circuit OPENED for model %s (%d failures in %ds window)",
                model, failure_count, self.config.window_seconds,
            )

    async def get_model_status(self, model: str) -> dict:
        """获取模型熔断状态（给管理 API 用）。"""
        r = await get_redis()
        state = await self._get_state(r, model)
        failures_key = self._key(model, "failures")
        now = time.time()
        cutoff = now - self.config.window_seconds
        await r.zremrangebyscore(failures_key, 0, cutoff)
        failure_count = await r.zcard(failures_key)
        return {
            "model": model,
            "state": state.value,
            "recent_failures": failure_count,
            "failure_threshold": self.config.failure_threshold,
        }

    async def _get_state(self, r, model: str) -> CircuitState:
        raw = await r.get(self._key(model, "state"))
        if raw is None:
            return CircuitState.CLOSED
        val = raw.decode() if isinstance(raw, bytes) else raw
        return CircuitState(val)

    async def _set_state(self, r, model: str, state: CircuitState) -> None:
        await r.set(self._key(model, "state"), state.value, ex=self.config.window_seconds * 2)


circuit_breaker = CircuitBreaker()
