import logging
import time

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
# Popular slugs (curated list from ClawHub)
# ---------------------------------------------------------------------------

_POPULAR_SLUGS = [
    "agentic-coding",
    "vibe-coding",
    "coding-lead",
    "business-writing",
    "writing-assistant",
    "human-writing",
    "market-research",
    "parallel-ai-research",
    "personal-productivity",
    "git-essentials",
    "email-daily-summary",
    "creative-genius",
    "ai-data-analysis",
    "deep-debugging",
    "japanese-translation-and-tutor",
]

# In-memory cache: {"items": [...], "expires": float}
_popular_cache: dict = {"items": [], "expires": 0.0}

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

    # Normalise: ClawHub returns {results: [...]} — handle both old and new shapes.
    if isinstance(data, list):
        raw_items = data
        total = len(data)
    else:
        raw_items = (
            data.get("results")
            or data.get("items")
            or data.get("data")
            or []
        )
        total = data.get("total") or data.get("count") or len(raw_items)

    items = [
        ClawHubPlugin(
            slug=item.get("slug", ""),
            name=(
                item.get("displayName")
                or item.get("name")
                or item.get("title")
                or item.get("slug", "").replace("-", " ").title()
            ),
            description=item.get("summary") or item.get("description"),
            author=item.get("author") or item.get("author_name"),
            downloads=item.get("downloads") or item.get("download_count"),
            version=item.get("version") or item.get("latest_version"),
            tags=item.get("tags") or [],
        )
        for item in raw_items
        if item.get("slug") or item.get("name")
    ]

    return SearchResponse(items=items, total=total)


@router.get("/popular", response_model=SearchResponse)
async def popular_skills():
    """Return a curated list of popular skills fetched from ClawHub (1-hour cache)."""
    global _popular_cache

    now = time.time()
    if _popular_cache["expires"] > now and _popular_cache["items"]:
        cached = _popular_cache["items"]
        return SearchResponse(items=cached, total=len(cached))

    items: list[ClawHubPlugin] = []
    for slug in _POPULAR_SLUGS:
        try:
            data = await _clawhub_get(f"/skills/{slug}")
            skill = data.get("skill", {}) or data
            owner = data.get("owner") or {}
            latest = data.get("latestVersion") or {}
            stats = skill.get("stats") or {}
            raw_tags = skill.get("tags") or {}
            tag_list = list(raw_tags.keys()) if isinstance(raw_tags, dict) else raw_tags

            items.append(ClawHubPlugin(
                slug=skill.get("slug") or slug,
                name=skill.get("displayName") or slug.replace("-", " ").title(),
                description=skill.get("summary"),
                author=owner.get("displayName") or owner.get("handle"),
                downloads=stats.get("downloads"),
                version=latest.get("version"),
                tags=tag_list,
            ))
        except Exception as exc:
            logger.warning("Failed to fetch popular skill %s: %s", slug, exc)

    _popular_cache = {"items": items, "expires": now + 3600.0}
    return SearchResponse(items=items, total=len(items))


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
    """Execute `npx clawhub install <slug> --no-input` inside the agent container."""
    agent = await get_agent(db, body.agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not agent.container_id:
        raise HTTPException(status_code=400, detail="Agent container is not running")

    try:
        container = docker_manager.client.containers.get(agent.container_id)
        exit_code, output_bytes = container.exec_run(
            ["npx", "clawhub", "install", body.slug, "--no-input"],
            demux=False,
        )
    except Exception as exc:
        logger.error("Docker exec error for agent %s: %s", body.agent_id, exc)
        raise HTTPException(status_code=500, detail=f"Container exec error: {exc!s}"[:300])

    output = (output_bytes or b"").decode("utf-8", errors="replace")[:500]

    if exit_code != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Skill install failed (exit {exit_code}): {output}",
        )

    return InstallResponse(success=True, output=output)
