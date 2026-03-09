"""Tool Store service — catalog loading + agent tool management."""

import json
import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus

logger = logging.getLogger(__name__)

# Load catalog once at module import
_CATALOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "toolstore", "catalog.json"
)
_catalog: dict | None = None


def _load_catalog() -> dict:
    global _catalog
    if _catalog is None:
        with open(os.path.abspath(_CATALOG_PATH), encoding="utf-8") as f:
            _catalog = json.load(f)
    return _catalog


def get_catalog(category: str | None = None, search: str | None = None, locale: str = "en") -> dict:
    """Get tool catalog with optional filtering."""
    catalog = _load_catalog()
    tools = catalog["tools"]

    if category:
        tools = [t for t in tools if t["category"] == category]

    if search:
        q = search.lower()
        tools = [
            t for t in tools
            if q in t["name"].lower()
            or q in t.get("description", "").lower()
            or any(q in tag for tag in t.get("tags", []))
        ]

    # Localize names/descriptions
    localized_tools = []
    for t in tools:
        lt = {
            "id": t["id"],
            "name": t.get(f"name_{locale}", t["name"]),
            "type": t["type"],
            "category": t["category"],
            "description": t.get(f"description_{locale}", t["description"]),
            "icon": t["icon"],
            "author": t["author"],
            "tags": t["tags"],
            "popularity": t["popularity"],
        }
        localized_tools.append(lt)

    # Localize categories
    categories = []
    for c in catalog["categories"]:
        categories.append({
            "id": c["id"],
            "name": c.get(f"name_{locale}", c["name"]),
            "icon": c["icon"],
        })

    return {"tools": localized_tools, "categories": categories}


def get_popular(limit: int = 10, locale: str = "en") -> list[dict]:
    """Get most popular tools."""
    result = get_catalog(locale=locale)
    tools = sorted(result["tools"], key=lambda t: t["popularity"], reverse=True)
    return tools[:limit]


def get_tool_by_id(tool_id: str) -> dict | None:
    """Get raw tool definition by ID (with config)."""
    catalog = _load_catalog()
    for t in catalog["tools"]:
        if t["id"] == tool_id:
            return t
    return None


async def install_tool(db: AsyncSession, agent: Agent, tool_id: str) -> dict:
    """Install a tool to an agent."""
    tool = get_tool_by_id(tool_id)
    if tool is None:
        raise ToolNotFoundError(f"Tool '{tool_id}' not found in catalog")

    # Initialize config if needed
    config = agent.config or {}
    installed = config.get("installed_tools", [])

    if tool_id in installed:
        return {"status": "already_installed", "tool_id": tool_id, "needs_restart": False}

    installed.append(tool_id)
    config["installed_tools"] = installed

    # Store tool config for runtime use
    tool_configs = config.get("tool_configs", {})
    tool_configs[tool_id] = tool.get("config", {})
    config["tool_configs"] = tool_configs

    agent.config = config
    await db.commit()
    await db.refresh(agent)

    needs_restart = agent.status == AgentStatus.running
    return {"status": "installed", "tool_id": tool_id, "needs_restart": needs_restart}


async def uninstall_tool(db: AsyncSession, agent: Agent, tool_id: str) -> dict:
    """Remove a tool from an agent."""
    config = agent.config or {}
    installed = config.get("installed_tools", [])

    if tool_id not in installed:
        raise ToolNotFoundError(f"Tool '{tool_id}' is not installed on this agent")

    installed.remove(tool_id)
    config["installed_tools"] = installed

    # Remove tool config
    tool_configs = config.get("tool_configs", {})
    tool_configs.pop(tool_id, None)
    config["tool_configs"] = tool_configs

    agent.config = config
    await db.commit()
    await db.refresh(agent)

    needs_restart = agent.status == AgentStatus.running
    return {"status": "uninstalled", "tool_id": tool_id, "needs_restart": needs_restart}


def get_agent_tools(agent: Agent, locale: str = "en") -> list[dict]:
    """Get localized list of tools installed on an agent."""
    config = agent.config or {}
    installed = config.get("installed_tools", [])

    tools = []
    for tool_id in installed:
        tool = get_tool_by_id(tool_id)
        if tool:
            tools.append({
                "id": tool["id"],
                "name": tool.get(f"name_{locale}", tool["name"]),
                "type": tool["type"],
                "category": tool["category"],
                "description": tool.get(f"description_{locale}", tool["description"]),
                "icon": tool["icon"],
            })
    return tools


class ToolNotFoundError(Exception):
    pass
