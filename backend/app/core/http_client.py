"""Shared httpx AsyncClient with connection pooling.

Usage:
    from app.core.http_client import http_client

    async with http_client() as client:
        resp = await client.get("https://...")

Or for LiteLLM calls:
    from app.core.http_client import litellm_client

    async with litellm_client() as client:
        resp = await client.post(url, json=payload, headers=headers)
"""

import httpx

from app.config import settings

# Shared client pool — reused across all requests (connection pooling)
_shared_client: httpx.AsyncClient | None = None
_litellm_client: httpx.AsyncClient | None = None


def get_shared_client() -> httpx.AsyncClient:
    """Get or create the shared httpx client for external API calls."""
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            follow_redirects=True,
        )
    return _shared_client


def get_litellm_client() -> httpx.AsyncClient:
    """Get or create the shared httpx client for LiteLLM calls."""
    global _litellm_client
    if _litellm_client is None or _litellm_client.is_closed:
        _litellm_client = httpx.AsyncClient(
            base_url=settings.litellm_url,
            timeout=httpx.Timeout(120.0, connect=5.0),
            limits=httpx.Limits(max_connections=30, max_keepalive_connections=15),
            headers={
                "Authorization": f"Bearer {settings.litellm_master_key}",
                "Content-Type": "application/json",
            },
        )
    return _litellm_client


async def close_clients():
    """Close shared clients on app shutdown."""
    global _shared_client, _litellm_client
    if _shared_client and not _shared_client.is_closed:
        await _shared_client.aclose()
    if _litellm_client and not _litellm_client.is_closed:
        await _litellm_client.aclose()
