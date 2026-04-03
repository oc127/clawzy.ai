from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.v1.legal import router as legal_router
from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware

# Conditionally expose API docs (disabled in production)
_is_dev = settings.environment.lower() in ("development", "dev", "local", "test")
_docs_url = "/docs" if _is_dev else None
_redoc_url = "/redoc" if _is_dev else None

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# CORS — allow configured origins, plus localhost variants in development
_cors_origins = list(settings.cors_origins)
if _is_dev:
    _cors_origins += [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(legal_router)   # /privacy, /terms (root-level for Apple/legal)
app.include_router(api_router)


@app.on_event("startup")
async def validate_secrets():
    """Crash in production if secrets still contain placeholder defaults."""
    import sys

    warnings = []
    if "change-me" in settings.jwt_secret:
        warnings.append("jwt_secret contains default value! Set JWT_SECRET in .env")
    if "change-me" in settings.litellm_master_key:
        warnings.append("litellm_master_key contains default value! Set LITELLM_MASTER_KEY in .env")

    for w in warnings:
        print(f"CRITICAL: {w}", file=sys.stderr)

    if warnings and settings.environment.lower() == "production":
        print("FATAL: refusing to start with default secrets in production", file=sys.stderr)
        sys.exit(1)


@app.on_event("startup")
async def startup_event():
    from app.services.scheduler_service import start_scheduler
    start_scheduler()

    # Background task: refresh ClawHub popular cache every 2 hours
    import asyncio

    async def _refresh_clawhub_cache():
        """Pre-warm popular plugin caches for all languages every 2 hours."""
        import logging
        logger = logging.getLogger("clawhub_cache")
        await asyncio.sleep(10)  # Wait for app to fully start
        while True:
            for lang in ("ja", "zh", "ko", "en"):
                try:
                    from app.api.v1.clawhub import (
                        _popular_plugins, _translate_plugins, ClawHubPlugin,
                    )
                    from app.core.redis import get_redis
                    import json

                    rd = await get_redis()
                    limit = 10
                    cache_key = f"clawhub:popular:{lang}:{limit}"

                    items = await _popular_plugins(limit)
                    items = await _translate_plugins(items, lang)
                    await rd.set(
                        cache_key,
                        json.dumps([p.model_dump() for p in items], ensure_ascii=False),
                        ex=21600,
                    )
                    logger.info("Refreshed ClawHub popular cache: lang=%s, items=%d", lang, len(items))
                except Exception as exc:
                    logger.warning("ClawHub cache refresh failed for %s: %s", lang, exc)
            await asyncio.sleep(7200)  # Every 2 hours

    asyncio.create_task(_refresh_clawhub_cache())


@app.on_event("shutdown")
async def shutdown_event():
    from app.core.http_client import close_clients
    await close_clients()


@app.get("/health")
async def health():
    from app.core.docker_manager import docker_manager

    openclaw_status = "ok"
    try:
        docker_manager.client.ping()
    except Exception:
        openclaw_status = "offline"

    return {
        "status": "ok",
        "service": "nipponclaw-backend",
        "openclaw": openclaw_status,
    }
