import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401
from app.api.router import api_router
from app.config import settings
from app.core.database import Base, engine
from app.core.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)

# Columns added after initial deployment — ensure they exist on upgrade
_COLUMN_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_credit_limit INTEGER",
    "ALTER TABLE skills ADD COLUMN IF NOT EXISTS security_status VARCHAR(20) DEFAULT 'unreviewed'",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast only in production; warn otherwise
    if os.getenv("DEPLOY_ENV") == "production":
        if settings.jwt_secret in ("change-me-jwt-secret", ""):
            logger.critical(
                "JWT_SECRET is default in production! Set JWT_SECRET (openssl rand -hex 32)"
            )
            raise SystemExit(1)
        if settings.cors_origins.strip() == "*":
            logger.critical(
                "CORS_ORIGINS is '*' in production! Restrict to your domain"
            )
            raise SystemExit(1)
    elif not settings.debug:
        if settings.jwt_secret in ("change-me-jwt-secret", ""):
            logger.critical(
                "JWT_SECRET is default! Set JWT_SECRET in production (openssl rand -hex 32)"
            )
        if settings.cors_origins.strip() == "*":
            logger.warning(
                "CORS_ORIGINS is '*' — restrict to your domain in production"
            )
    # Create tables on startup (safe: CREATE IF NOT EXISTS)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Ensure newer columns exist (no-op if already present)
        for stmt in _COLUMN_MIGRATIONS:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                logger.warning("Migration skipped (%s): %s", stmt.split()[-1], e)
    logger.info("Database tables ready")

    # Start proactive engine scheduler (runs every 15 minutes)
    async def _proactive_loop():
        from app.services.proactive_engine import run_proactive_cycle
        from app.core.database import async_session

        while True:
            try:
                async with async_session() as db:
                    await run_proactive_cycle(db)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.debug("Proactive cycle error", exc_info=True)
            await asyncio.sleep(900)  # 15 minutes

    proactive_task = asyncio.create_task(_proactive_loop())
    logger.info("Proactive engine scheduler started (15 min interval)")

    yield

    proactive_task.cancel()
    try:
        await proactive_task
    except asyncio.CancelledError:
        pass


_is_production = os.getenv("DEPLOY_ENV") == "production"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    # Disable API docs in production
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
    lifespan=lifespan,
)

# Parse CORS origins from config (comma-separated or "*")
_cors_origins = (
    ["*"]
    if settings.cors_origins.strip() == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "lucy-backend"}
