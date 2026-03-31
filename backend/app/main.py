from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
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

app.include_router(api_router)


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
        "service": "clawzy-backend",
        "openclaw": openclaw_status,
    }
