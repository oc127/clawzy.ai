import logging
import secrets

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.docker_manager import docker_manager
from app.models.agent import Agent, AgentStatus
from app.models.subscription import Subscription, PlanType, SubStatus

logger = logging.getLogger(__name__)

# Agent limits per plan
PLAN_AGENT_LIMITS: dict[str, int] = {
    "free": 1,
    "starter": 1,
    "pro": 3,
    "business": 10,
}


class AgentLimitError(Exception):
    pass


async def get_user_plan(db: AsyncSession, user_id: str) -> str:
    result = await db.execute(
        select(Subscription.plan)
        .where(Subscription.user_id == user_id, Subscription.status == SubStatus.active)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    return plan.value if plan else "free"


async def count_user_agents(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(func.count()).where(Agent.user_id == user_id)
    )
    return result.scalar_one()


async def create_agent(db: AsyncSession, user_id: str, name: str, model_name: str) -> Agent:
    """Create a new agent record and provision an OpenClaw container."""
    plan = await get_user_plan(db, user_id)
    count = await count_user_agents(db, user_id)
    limit = PLAN_AGENT_LIMITS.get(plan, 1)

    if count >= limit:
        raise AgentLimitError(f"Plan '{plan}' allows max {limit} agent(s). You have {count}.")

    # Allocate a WS port
    ws_port = await allocate_port(db)

    # Generate a unique gateway token for this agent
    gateway_token = secrets.token_hex(32)

    agent = Agent(
        user_id=user_id,
        name=name,
        model_name=model_name,
        status=AgentStatus.creating,
        ws_port=ws_port,
        gateway_token=gateway_token,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # Provision the OpenClaw container
    try:
        container_id = docker_manager.create_agent_container(
            agent_id=agent.id,
            gateway_token=gateway_token,
            litellm_key=settings.litellm_master_key,
            model_name=model_name,
            ws_port=ws_port,
        )
        agent.container_id = container_id
        # Wait for container to be healthy before marking as running
        if docker_manager.wait_for_healthy(agent.id, timeout=30):
            agent.status = AgentStatus.running
        else:
            logger.warning("Agent %s container started but not healthy yet", agent.id)
            agent.status = AgentStatus.running  # still mark running, chat will use shared gateway as fallback
    except Exception as e:
        logger.error("Failed to create container for agent %s: %s", agent.id, e)
        agent.status = AgentStatus.error
    await db.commit()
    await db.refresh(agent)
    return agent


async def allocate_port(db: AsyncSession) -> int:
    """Find the next available WS port.

    Uses a gap-finding query to handle non-contiguous port ranges
    (e.g. if an agent in the middle was deleted). Falls back to
    max(port)+1 when there are no gaps.
    """
    # Get all currently allocated ports
    result = await db.execute(
        select(Agent.ws_port)
        .where(Agent.ws_port.isnot(None))
        .order_by(Agent.ws_port.asc())
    )
    used_ports = set(result.scalars().all())

    if not used_ports:
        return settings.openclaw_port_start

    # Try to find a gap in the range
    for port in range(settings.openclaw_port_start, settings.openclaw_port_end + 1):
        if port not in used_ports:
            return port

    raise RuntimeError("No available ports")


async def list_agents(db: AsyncSession, user_id: str) -> list[Agent]:
    result = await db.execute(
        select(Agent).where(Agent.user_id == user_id).order_by(Agent.created_at.desc())
    )
    return list(result.scalars().all())


async def get_agent(db: AsyncSession, agent_id: str, user_id: str) -> Agent | None:
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_agent(db: AsyncSession, agent: Agent, name: str | None, model_name: str | None) -> Agent:
    if name is not None:
        agent.name = name
    if model_name is not None:
        agent.model_name = model_name
    await db.commit()
    await db.refresh(agent)
    return agent


async def delete_agent(db: AsyncSession, agent: Agent) -> None:
    if agent.container_id:
        docker_manager.remove_container(agent.container_id, agent_id=agent.id)
    await db.delete(agent)
    await db.commit()


async def start_agent(db: AsyncSession, agent: Agent) -> Agent:
    """Start a stopped agent's container."""
    if not agent.container_id:
        raise ValueError("Agent has no container")
    docker_manager.start_container(agent.container_id)
    agent.status = AgentStatus.running
    await db.commit()
    await db.refresh(agent)
    return agent


async def stop_agent(db: AsyncSession, agent: Agent) -> Agent:
    """Stop a running agent's container."""
    if not agent.container_id:
        raise ValueError("Agent has no container")
    docker_manager.stop_container(agent.container_id)
    agent.status = AgentStatus.stopped
    await db.commit()
    await db.refresh(agent)
    return agent


async def restart_agent(db: AsyncSession, agent: Agent) -> Agent:
    """Restart an agent's container (quick recovery)."""
    if not agent.container_id:
        raise ValueError("Agent has no container")
    docker_manager.restart_container(agent.container_id)
    agent.status = AgentStatus.running
    await db.commit()
    await db.refresh(agent)
    return agent


def get_agent_health(agent: Agent) -> dict:
    """Get agent container health details."""
    if not agent.container_id:
        return {"status": "no_container", "running": False}
    return docker_manager.get_container_health(agent.container_id)


def get_agent_logs(agent: Agent, tail: int = 50) -> str:
    """Get agent container logs."""
    if not agent.container_id:
        return ""
    return docker_manager.get_container_logs(agent.container_id, tail=tail)
