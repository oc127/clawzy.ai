"""Redis-based fixed-window rate limiting middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as redis

from app.core.redis import redis_pool
from app.core.security import decode_token

# (max_requests, window_seconds)
_AUTH_LIMIT = (5, 60)
_CHAT_LIMIT = (30, 60)
_API_LIMIT = (60, 60)

_AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _extract_user_id(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_token(auth[7:])
        if payload and payload.get("type") == "access":
            return payload.get("sub")
    return None


async def _check_limit(r: redis.Redis, key: str, limit: int, window: int) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, window)
    return count <= limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip non-API paths
        if not path.startswith("/api/v1/"):
            return await call_next(request)

        if path in _AUTH_PATHS:
            limit, window = _AUTH_LIMIT
            identifier = _get_client_ip(request)
            key = f"rl:auth:{identifier}"
        elif "/chat" in path:
            limit, window = _CHAT_LIMIT
            user_id = _extract_user_id(request)
            identifier = user_id or _get_client_ip(request)
            key = f"rl:chat:{identifier}"
        else:
            limit, window = _API_LIMIT
            user_id = _extract_user_id(request)
            identifier = user_id or _get_client_ip(request)
            key = f"rl:api:{identifier}"

        try:
            r = redis.Redis(connection_pool=redis_pool)
            allowed = await _check_limit(r, key, limit, window)
        except Exception:
            # Redis unavailable — fail open
            return await call_next(request)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests, please slow down."},
                headers={"Retry-After": str(window)},
            )

        return await call_next(request)
