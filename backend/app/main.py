import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.logging_config import setup_logging
from app.i18n import parse_locale
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)

# 初始化结构化日志
setup_logging(json_format=not settings.debug)

# Sentry error tracking
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        environment="production" if not settings.debug else "development",
    )

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- 中间件（后添加的先执行） ---

@app.middleware("http")
async def locale_middleware(request, call_next):
    """Parse locale from cookie / Accept-Language and store in request.state."""
    locale = parse_locale(
        request.headers.get("accept-language"),
        request.cookies.get("locale"),
    )
    request.state.locale = locale
    response = await call_next(request)
    return response

app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.app_url,
        settings.app_url.replace("://", "://www."),
        "http://localhost:3000",  # 本地开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup_checks():
    """验证关键依赖可用，不可用则启动失败（Docker 会自动重启）。"""
    from app.services.health_service import check_database, check_redis, HealthStatus

    db_result = await check_database()
    if db_result.status == HealthStatus.UNHEALTHY:
        logger.critical("PostgreSQL unavailable at startup: %s", db_result.details)
        raise RuntimeError(f"Database not available: {db_result.details}")

    redis_result = await check_redis()
    if redis_result.status == HealthStatus.UNHEALTHY:
        logger.critical("Redis unavailable at startup: %s", redis_result.details)
        raise RuntimeError(f"Redis not available: {redis_result.details}")

    logger.info("Startup checks passed (DB: %.0fms, Redis: %.0fms)",
                db_result.latency_ms, redis_result.latency_ms)

    # Start Telegram bot polling in background (if configured)
    if settings.telegram_bot_token:
        from app.integrations.telegram_bot import start_polling
        asyncio.create_task(start_polling())


@app.on_event("shutdown")
async def shutdown():
    """优雅关机：等待 in-flight 请求完成。"""
    logger.info("Shutting down gracefully, waiting for in-flight requests...")
    await asyncio.sleep(5)
    logger.info("Shutdown complete")


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
