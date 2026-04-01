"""MCP service — manage Model Context Protocol servers for agents."""

import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.docker_manager import docker_manager
from app.models.mcp import AgentMCPServer

logger = logging.getLogger(__name__)


async def list_mcp_servers(db: AsyncSession, agent_id: str) -> list[AgentMCPServer]:
    """List all MCP servers configured for an agent."""
    result = await db.execute(
        select(AgentMCPServer)
        .where(AgentMCPServer.agent_id == agent_id)
        .order_by(AgentMCPServer.created_at.desc())
    )
    return list(result.scalars().all())


async def get_mcp_server(db: AsyncSession, server_id: str) -> AgentMCPServer | None:
    """Get a single MCP server by ID."""
    result = await db.execute(
        select(AgentMCPServer).where(AgentMCPServer.id == server_id)
    )
    return result.scalar_one_or_none()


async def add_mcp_server(
    db: AsyncSession,
    agent_id: str,
    name: str,
    transport: str,
    command: str | None = None,
    url: str | None = None,
    config: dict | None = None,
) -> AgentMCPServer:
    """Add a new MCP server configuration to an agent."""
    server = AgentMCPServer(
        agent_id=agent_id,
        name=name,
        transport=transport,
        command=command,
        url=url,
        config=config,
        enabled=True,
    )
    db.add(server)
    await db.commit()
    await db.refresh(server)
    logger.info("Added MCP server '%s' (%s) to agent %s", name, transport, agent_id)
    return server


async def discover_tools(agent_id: str, server: AgentMCPServer) -> list[dict]:
    """
    Discover available tools from an MCP server.

    For HTTP transport, calls the MCP server's tools/list endpoint.
    For stdio transport, executes the command in the agent container.
    """
    if server.transport == "http" and server.url:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{server.url.rstrip('/')}/tools/list",
                    json={},
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("tools", [])
        except Exception as exc:
            logger.error("Failed to discover tools from HTTP MCP server %s: %s", server.name, exc)
            return []

    elif server.transport == "stdio" and server.command:
        # Run the MCP command inside the agent's container to list tools
        try:
            from app.models.agent import Agent
            # We need the container_id — caller should ensure agent is running
            container = docker_manager.client.containers.get(f"clawzy-agent-{agent_id}")
            exit_code, output_bytes = container.exec_run(
                ["sh", "-c", f"{server.command} --list-tools"],
                demux=False,
            )
            output = (output_bytes or b"").decode("utf-8", errors="replace")
            if exit_code == 0:
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    logger.warning("Non-JSON tool list from MCP server '%s'", server.name)
                    return []
        except Exception as exc:
            logger.error("Failed to discover tools from stdio MCP server %s: %s", server.name, exc)
            return []

    return []


async def execute_mcp_tool(
    agent_id: str,
    server: AgentMCPServer,
    tool_name: str,
    arguments: dict | None = None,
) -> dict:
    """Execute a tool on an MCP server."""
    if server.transport == "http" and server.url:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{server.url.rstrip('/')}/tools/call",
                    json={"name": tool_name, "arguments": arguments or {}},
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("MCP tool execution failed (%s/%s): %s", server.name, tool_name, exc)
            return {"error": str(exc)}

    elif server.transport == "stdio" and server.command:
        try:
            container = docker_manager.client.containers.get(f"clawzy-agent-{agent_id}")
            tool_input = json.dumps({"name": tool_name, "arguments": arguments or {}})
            exit_code, output_bytes = container.exec_run(
                ["sh", "-c", f"echo '{tool_input}' | {server.command}"],
                demux=False,
            )
            output = (output_bytes or b"").decode("utf-8", errors="replace")
            if exit_code == 0:
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return {"result": output}
            return {"error": f"Exit code {exit_code}: {output[:500]}"}
        except Exception as exc:
            logger.error("MCP tool execution failed (%s/%s): %s", server.name, tool_name, exc)
            return {"error": str(exc)}

    return {"error": "Unsupported transport"}


async def remove_mcp_server(db: AsyncSession, server_id: str) -> bool:
    """Remove an MCP server configuration."""
    server = await get_mcp_server(db, server_id)
    if server is None:
        return False
    await db.delete(server)
    await db.commit()
    return True
