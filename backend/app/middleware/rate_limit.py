"""限流中间件 — Redis 滑动窗口，防止 API 滥用。"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.redis import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """每 IP 每分钟最多 N 次 API 请求。"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rpm = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        # WebSocket 不限流（有自己的流控）
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"clawzy:ratelimit:{client_ip}"

        try:
            r = await get_redis()
            now = time.time()
            window_start = now - 60

            pipe = r.pipeline()
            pipe.zadd(key, {str(now): now})
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.expire(key, 120)
            results = await pipe.execute()

            request_count = results[2]

            if request_count > self.rpm:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求太频繁了，请稍后再试"},
                    headers={"Retry-After": "60"},
                )
        except Exception:
            pass  # Redis 挂了不阻塞请求

        return await call_next(request)
