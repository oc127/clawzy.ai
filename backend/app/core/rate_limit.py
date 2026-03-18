"""In-memory rate limiting middleware with periodic cleanup.

Per-IP rate limiting for general endpoints and stricter limits for auth.
"""

import logging
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory store: {key: [timestamp, ...]}
_store: dict[str, list[float]] = defaultdict(list)
_last_cleanup: float = 0.0
_CLEANUP_INTERVAL = 300.0  # Clean up stale keys every 5 minutes

# Auth paths get stricter limits
_AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"}


def _get_client_ip(request: Request) -> str:
    """Extract client IP. Only trust X-Forwarded-For from known proxy (first hop)."""
    # In Docker, requests come through nginx — use X-Real-IP set by nginx
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def _cleanup_old_entries(entries: list[float], window: float) -> list[float]:
    cutoff = time.time() - window
    return [t for t in entries if t > cutoff]


def _cleanup_stale_keys() -> None:
    """Remove keys that have no recent entries to prevent unbounded memory growth."""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    stale_keys = [k for k, v in _store.items() if not v]
    for k in stale_keys:
        del _store[k]


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        client_ip = _get_client_ip(request)
        now = time.time()
        window = 60.0  # 1 minute window

        is_auth = path in _AUTH_PATHS
        limit = settings.rate_limit_auth_per_minute if is_auth else settings.rate_limit_per_minute

        key = f"{client_ip}:{'auth' if is_auth else 'general'}"

        # Clean up and check
        _store[key] = _cleanup_old_entries(_store[key], window)
        _cleanup_stale_keys()

        if len(_store[key]) >= limit:
            retry_after = int(window - (now - _store[key][0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(max(1, retry_after))},
            )

        _store[key].append(now)
        return await call_next(request)
