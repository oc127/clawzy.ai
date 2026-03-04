import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    retry_on_timeout=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


async def get_redis() -> redis.Redis:
    """获取 Redis 连接，带连接验证。"""
    r = redis.Redis(connection_pool=redis_pool)
    try:
        await r.ping()
    except Exception:
        logger.warning("Redis ping failed, connection may be unhealthy")
    return r
