"""Tool service — built-in tools that agents can invoke during chat."""

import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.docker_manager import docker_manager
from app.models.tool import AgentTool
from app.services.workspace_service import (
    WORKSPACE_ROOT,
    list_files,
    read_file,
    write_file,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in tool definitions (OpenAI function-calling format)
# ---------------------------------------------------------------------------

BUILTIN_TOOLS: dict[str, dict] = {
    "web_search": {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns search results with titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                },
                "required": ["query"],
            },
        },
    },
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": f"File path (relative to {WORKSPACE_ROOT} or absolute)",
                    },
                },
                "required": ["path"],
            },
        },
    },
    "write_file": {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": f"File path (relative to {WORKSPACE_ROOT} or absolute)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    "list_files": {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": f"Directory path (default: {WORKSPACE_ROOT})",
                    },
                },
                "required": [],
            },
        },
    },
    "execute_command": {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command inside the agent workspace. Use for running scripts, installing packages, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute",
                    },
                },
                "required": ["command"],
            },
        },
    },
}


async def get_enabled_tools(db: AsyncSession, agent_id: str) -> list[dict]:
    """Return OpenAI-format tool definitions for enabled tools."""
    result = await db.execute(
        select(AgentTool).where(
            AgentTool.agent_id == agent_id,
            AgentTool.enabled == True,  # noqa: E712
        )
    )
    agent_tools = result.scalars().all()

    # If no tool records exist, return all builtins as default
    if not agent_tools:
        return list(BUILTIN_TOOLS.values())

    enabled = []
    for at in agent_tools:
        if at.tool_name in BUILTIN_TOOLS:
            enabled.append(BUILTIN_TOOLS[at.tool_name])
    return enabled


async def get_tools_status(db: AsyncSession, agent_id: str) -> list[dict]:
    """Return all tools with their enabled/approval status."""
    result = await db.execute(
        select(AgentTool).where(AgentTool.agent_id == agent_id)
    )
    existing = {t.tool_name: t for t in result.scalars().all()}

    tools = []
    for name, definition in BUILTIN_TOOLS.items():
        if name in existing:
            t = existing[name]
            tools.append({
                "tool_name": name,
                "description": definition["function"]["description"],
                "enabled": t.enabled,
                "requires_approval": t.requires_approval,
            })
        else:
            # Default: enabled, no approval required
            tools.append({
                "tool_name": name,
                "description": definition["function"]["description"],
                "enabled": True,
                "requires_approval": False,
            })
    return tools


async def update_tool(
    db: AsyncSession,
    agent_id: str,
    tool_name: str,
    enabled: bool | None = None,
    requires_approval: bool | None = None,
) -> dict:
    """Enable/disable a tool or set approval requirement."""
    if tool_name not in BUILTIN_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    result = await db.execute(
        select(AgentTool).where(
            AgentTool.agent_id == agent_id,
            AgentTool.tool_name == tool_name,
        )
    )
    tool = result.scalar_one_or_none()

    if tool is None:
        tool = AgentTool(
            agent_id=agent_id,
            tool_name=tool_name,
            enabled=enabled if enabled is not None else True,
            requires_approval=requires_approval if requires_approval is not None else False,
        )
        db.add(tool)
    else:
        if enabled is not None:
            tool.enabled = enabled
        if requires_approval is not None:
            tool.requires_approval = requires_approval

    await db.commit()

    return {
        "tool_name": tool_name,
        "enabled": tool.enabled,
        "requires_approval": tool.requires_approval,
    }


# ---------------------------------------------------------------------------
# Tool execution handlers
# ---------------------------------------------------------------------------


def _resolve_path(path: str) -> str:
    """Resolve a potentially relative path to an absolute workspace path."""
    if path.startswith("/"):
        return path
    return f"{WORKSPACE_ROOT}/{path}"


async def _handle_read_file(container_id: str, arguments: dict) -> str:
    path = _resolve_path(arguments["path"])
    try:
        content = await read_file(container_id, path)
        return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"


async def _handle_write_file(container_id: str, arguments: dict) -> str:
    path = _resolve_path(arguments["path"])
    await write_file(container_id, path, arguments["content"])
    return f"File written successfully: {path}"


async def _handle_list_files(container_id: str, arguments: dict) -> str:
    path = _resolve_path(arguments.get("path", WORKSPACE_ROOT))
    entries = await list_files(container_id, path)
    if not entries:
        return f"No files found in {path}"
    lines = []
    for e in entries:
        prefix = "[DIR]" if e["type"] == "directory" else f"[{e['size']}B]"
        lines.append(f"  {prefix} {e['name']}")
    return f"Contents of {path}:\n" + "\n".join(lines)


async def _handle_execute_command(container_id: str, arguments: dict) -> str:
    command = arguments["command"]
    container = docker_manager.client.containers.get(container_id)
    exit_code, output_bytes = container.exec_run(
        ["sh", "-c", command],
        workdir=WORKSPACE_ROOT,
        demux=False,
    )
    output = (output_bytes or b"").decode("utf-8", errors="replace")[:4000]
    if exit_code != 0:
        return f"Command failed (exit {exit_code}):\n{output}"
    return output or "(no output)"


async def _handle_web_search(arguments: dict) -> str:
    """Basic web search via DuckDuckGo HTML (no API key needed)."""
    query = arguments["query"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Clawzy-Agent/1.0"},
            )
            resp.raise_for_status()
            # Extract text snippets (basic parsing)
            from html.parser import HTMLParser

            class ResultParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self._in_result = False
                    self._current = ""

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                        self._in_result = True
                        self._current = ""

                def handle_data(self, data):
                    if self._in_result:
                        self._current += data

                def handle_endtag(self, tag):
                    if tag == "a" and self._in_result:
                        self._in_result = False
                        if self._current.strip():
                            self.results.append(self._current.strip())

            parser = ResultParser()
            parser.feed(resp.text)

            if parser.results:
                return "Search results:\n" + "\n".join(
                    f"  {i+1}. {r}" for i, r in enumerate(parser.results[:5])
                )
            return f"No results found for: {query}"

    except Exception as exc:
        return f"Search failed: {exc}"


# Dispatch table
_HANDLERS = {
    "read_file": lambda cid, args: _handle_read_file(cid, args),
    "write_file": lambda cid, args: _handle_write_file(cid, args),
    "list_files": lambda cid, args: _handle_list_files(cid, args),
    "execute_command": lambda cid, args: _handle_execute_command(cid, args),
}


async def execute_tool(
    agent_id: str,
    container_id: str | None,
    tool_name: str,
    arguments: dict,
) -> str:
    """Dispatch a tool call and return the result as a string."""
    if tool_name == "web_search":
        return await _handle_web_search(arguments)

    if tool_name in _HANDLERS:
        if not container_id:
            return f"Error: Agent container is not running. Cannot execute {tool_name}."
        return await _HANDLERS[tool_name](container_id, arguments)

    return f"Error: Unknown tool '{tool_name}'"
