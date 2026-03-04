from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.logging_config import setup_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# 初始化结构化日志
setup_logging(json_format=not settings.debug)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- 中间件（后添加的先执行） ---
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://clawzy.ai",
        "https://www.clawzy.ai",
        "http://localhost:3000",  # 本地开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    """基础健康检查（Docker healthcheck / 负载均衡器用）。"""
    return {"status": "ok", "service": "clawzy-backend"}


@app.get("/health/deep")
async def health_deep():
    """深度健康检查 — 验证 DB、Redis、LiteLLM 全链路。"""
    from app.services.health_service import run_all_health_checks, HealthStatus
    results = await run_all_health_checks()

    any_unhealthy = any(r.status == HealthStatus.UNHEALTHY for r in results)
    return {
        "status": "degraded" if any_unhealthy else "ok",
        "checks": [
            {"service": r.service, "status": r.status.value, "latency_ms": round(r.latency_ms, 1)}
            for r in results
        ],
    }
