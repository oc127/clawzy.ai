import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.config import settings
from app.core.database import engine, Base

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401

logger = logging.getLogger(__name__)

# Columns added after initial deployment — ensure they exist on upgrade
_COLUMN_MIGRATIONS = [
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS gateway_token VARCHAR(100)",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS container_id VARCHAR(100)",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS ws_port INTEGER",
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
            except Exception:
                pass
    logger.info("Database tables ready")
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to clawzy.ai in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "clawzy-backend"}
