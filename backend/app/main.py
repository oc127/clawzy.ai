import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings

logger = logging.getLogger(__name__)

# Validate critical secrets at startup
if not settings.jwt_secret:
    raise RuntimeError("JWT_SECRET environment variable must be set")
if not settings.litellm_master_key:
    raise RuntimeError("LITELLM_MASTER_KEY environment variable must be set")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "clawzy-backend"}
