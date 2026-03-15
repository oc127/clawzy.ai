"""Simple in-memory rate limiting middleware.

Uses Redis when available, falls back to in-memory dict.
Per-IP rate limiting for general endpoints and stricter limits for auth.
"""

import time
import logging
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory store: {ip: [(timestamp, ...)]]}
_store: dict[str, list[float]] = defaultdict(list)

# Auth paths get stricter limits
_AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _cleanup_old_entries(entries: list[float], window: float) -> list[float]:
    cutoff = time.time() - window
    return [t for t in entries if t > cutoff]


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

        if len(_store[key]) >= limit:
            retry_after = int(window - (now - _store[key][0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(max(1, retry_after))},
            )

        _store[key].append(now)
        return await call_next(request)
