"""关联 ID 中间件 — 每个请求分配唯一 ID，方便全链路追踪。"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import correlation_id_var


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
        correlation_id_var.set(cid)

        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response
