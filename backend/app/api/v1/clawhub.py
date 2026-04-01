import asyncio
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

# Popular keywords used to build curated results when query is empty
_POPULAR_KEYWORDS = ["coding", "writing", "assistant", "data", "research"]

router = APIRouter(prefix="/clawhub", tags=["clawhub"])


# ---------------------------------------------------------------------------
# Shared HTTP helper
# ---------------------------------------------------------------------------

async def _clawhub_get(path: str, params: dict | None = None) -> dict | list:
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


async def _clawhub_get_safe(path: str, params: dict | None = None) -> dict | list | None:
    """Like _clawhub_get but returns None on error instead of raising."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{CLAWHUB_BASE}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


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
# Helpers
# ---------------------------------------------------------------------------

def _normalise_search_item(item: dict) -> ClawHubPlugin | None:
    """Turn a raw ClawHub search result into a ClawHubPlugin."""
    slug = item.get("slug", "")
    name = (
        item.get("name")
        or item.get("displayName")
        or item.get("title")
        or slug.replace("-", " ").title()
    )
    if not slug and not name:
        return None
    return ClawHubPlugin(
        slug=slug,
        name=name,
        description=item.get("description") or item.get("summary"),
        author=item.get("author") or item.get("author_name"),
        downloads=item.get("downloads") or item.get("download_count"),
        version=item.get("version") or item.get("latest_version"),
        tags=item.get("tags") if isinstance(item.get("tags"), list) else [],
    )


def _extract_items(data: dict | list) -> tuple[list[dict], int]:
    """Extract raw items list and total from a ClawHub response."""
    if isinstance(data, list):
        return data, len(data)
    raw = data.get("items") or data.get("results") or data.get("data") or []
    total = data.get("total") or data.get("count") or len(raw)
    return raw, total


async def _enrich_plugin(plugin: ClawHubPlugin) -> ClawHubPlugin:
    """Fetch detail for a single plugin to fill in author/downloads/version."""
    detail = await _clawhub_get_safe(f"/skills/{plugin.slug}")
    if not detail or not isinstance(detail, dict):
        return plugin
    skill = detail.get("skill", {})
    owner = detail.get("owner", {})
    latest = detail.get("latestVersion", {})
    stats = skill.get("stats", {})
    tag_info = skill.get("tags", {})

    return ClawHubPlugin(
        slug=plugin.slug,
        name=plugin.name,
        description=plugin.description,
        author=plugin.author or owner.get("handle") or owner.get("displayName"),
        downloads=plugin.downloads or stats.get("downloads"),
        version=plugin.version or latest.get("version") or tag_info.get("latest"),
        tags=plugin.tags if plugin.tags else list(tag_info.keys()) if isinstance(tag_info, dict) else [],
    )


async def _popular_plugins(limit: int) -> list[ClawHubPlugin]:
    """Build a curated popular list by merging results from several keywords."""

    async def _search_kw(kw: str) -> list[dict]:
        data = await _clawhub_get_safe("/search", params={"q": kw, "page": 1, "limit": 8})
        if data is None:
            return []
        items, _ = _extract_items(data)
        return items

    results = await asyncio.gather(*[_search_kw(kw) for kw in _POPULAR_KEYWORDS])

    seen: set[str] = set()
    merged: list[ClawHubPlugin] = []
    for items in results:
        for raw in items:
            p = _normalise_search_item(raw)
            if p and p.slug not in seen:
                seen.add(p.slug)
                merged.append(p)

    merged = merged[:limit]

    # Enrich with full metadata in parallel
    enriched = await asyncio.gather(*[_enrich_plugin(p) for p in merged])
    return list(enriched)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/search", response_model=SearchResponse)
async def search_plugins(
    q: str = "",
    page: int = 1,
    limit: int = 20,
):
    """Proxy ClawHub search. Empty query returns curated popular results."""

    # Empty query → return curated popular list (server-side, single request from iOS)
    if not q.strip():
        items = await _popular_plugins(limit)
        return SearchResponse(items=items, total=len(items))

    data = await _clawhub_get("/search", params={"q": q, "page": page, "limit": limit})
    raw_items, total = _extract_items(data)

    items = [p for raw in raw_items if (p := _normalise_search_item(raw)) is not None]

    # Enrich top results with full metadata (cap to avoid too many requests)
    if items:
        enriched = await asyncio.gather(*[_enrich_plugin(p) for p in items[:limit]])
        items = list(enriched)

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
