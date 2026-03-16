import logging
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
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS gateway_token VARCHAR(100)",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS container_id VARCHAR(100)",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS ws_port INTEGER",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_credit_limit INTEGER",
    "ALTER TABLE skills ADD COLUMN IF NOT EXISTS security_status VARCHAR(20) DEFAULT 'unreviewed'",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    return {"status": "ok", "service": "clawzy-backend"}
