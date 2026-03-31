import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.docker_manager import docker_manager
from app.deps import get_current_user
from app.models.user import User
from app.services.agent_service import get_agent

logger = logging.getLogger(__name__)

CLAWHUB_BASE = "https://clawhub.ai/api/v1"
_TIMEOUT = 10.0

router = APIRouter(prefix="/clawhub", tags=["clawhub"])


# ---------------------------------------------------------------------------
# Shared HTTP helper
# ---------------------------------------------------------------------------

async def _clawhub_get(path: str, params: dict | None = None) -> dict:
    """Proxy a GET request to ClawHub and return the JSON body."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{CLAWHUB_BASE}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="ClawHub request timed out")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"ClawHub returned {exc.response.status_code}",
        )
    except Exception as exc:
        logger.warning("ClawHub proxy error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to reach ClawHub")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ClawHubPlugin(BaseModel):
    slug: str
    name: str
    description: str | None = None
    author: str | None = None
    downloads: int | None = None
    version: str | None = None
    tags: list[str] = []


class SearchResponse(BaseModel):
    items: list[ClawHubPlugin]
    total: int


class InstallRequest(BaseModel):
    agent_id: str
    slug: str
    version: str = "latest"


class InstallResponse(BaseModel):
    success: bool
    output: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/search", response_model=SearchResponse)
async def search_plugins(
    q: str = "",
    page: int = 1,
    limit: int = 20,
):
    """Proxy ClawHub search. Returns a normalised plugin list."""
    data = await _clawhub_get("/search", params={"q": q, "page": page, "limit": limit})

    # Normalise: ClawHub may return {items, total} or a flat list — handle both.
    if isinstance(data, list):
        raw_items = data
        total = len(data)
    else:
        raw_items = data.get("items") or data.get("results") or data.get("data") or []
        total = data.get("total") or data.get("count") or len(raw_items)

    items = [
        ClawHubPlugin(
            slug=item.get("slug", ""),
            name=item.get("name") or item.get("title") or item.get("slug", "").replace("-", " ").title(),
            description=item.get("description") or item.get("summary"),
            author=item.get("author") or item.get("author_name"),
            downloads=item.get("downloads") or item.get("download_count"),
            version=item.get("version") or item.get("latest_version"),
            tags=item.get("tags") or [],
        )
        for item in raw_items
        if item.get("slug") or item.get("name")
    ]

    return SearchResponse(items=items, total=total)


@router.get("/skills/{slug}")
async def get_plugin(slug: str):
    """Proxy ClawHub skill detail endpoint."""
    return await _clawhub_get(f"/skills/{slug}")


@router.post("/install", response_model=InstallResponse)
async def install_plugin(
    body: InstallRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute `openclaw plugins install clawhub:<slug>` inside the agent container."""
    agent = await get_agent(db, body.agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not agent.container_id:
        raise HTTPException(status_code=400, detail="Agent container is not running")

    pkg = f"clawhub:{body.slug}"
    if body.version and body.version != "latest":
        pkg = f"{pkg}@{body.version}"

    try:
        container = docker_manager.client.containers.get(agent.container_id)
        exit_code, output_bytes = container.exec_run(
            ["openclaw", "plugins", "install", pkg],
            demux=False,
        )
    except Exception as exc:
        logger.error("Docker exec error for agent %s: %s", body.agent_id, exc)
        raise HTTPException(status_code=500, detail=f"Container exec error: {exc!s}"[:300])

    output = (output_bytes or b"").decode("utf-8", errors="replace")[:500]

    if exit_code != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Plugin install failed (exit {exit_code}): {output}",
        )

    return InstallResponse(success=True, output=output)
