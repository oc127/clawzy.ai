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


class AgentProvisionError(Exception):
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
        select(func.count(Agent.id)).where(Agent.user_id == user_id)
    )
    return result.scalar_one()


async def allocate_port(db: AsyncSession) -> int:
    """Find the next available WS port."""
    result = await db.execute(
        select(Agent.ws_port)
        .where(Agent.ws_port.isnot(None))
        .order_by(Agent.ws_port.desc())
        .limit(1)
    )
    last_port = result.scalar_one_or_none()
    next_port = (last_port + 1) if last_port else settings.openclaw_port_start
    if next_port > settings.openclaw_port_end:
        raise RuntimeError("No available ports")
    return next_port


async def create_agent(db: AsyncSession, user_id: str, name: str, model_name: str) -> Agent:
    """Create a new agent and provision an OpenClaw container."""
    plan = await get_user_plan(db, user_id)
    count = await count_user_agents(db, user_id)
    limit = PLAN_AGENT_LIMITS.get(plan, 1)

    if count >= limit:
        raise AgentLimitError(f"Plan '{plan}' allows max {limit} agent(s). You have {count}.")

    ws_port = await allocate_port(db)
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

    # Provision OpenClaw container
    try:
        container_id = docker_manager.create_agent_container(
            agent_id=agent.id,
            gateway_token=gateway_token,
            litellm_key=settings.litellm_master_key,
            model_name=model_name,
            ws_port=ws_port,
        )
        agent.container_id = container_id
        agent.status = AgentStatus.running
    except Exception as e:
        logger.error("Failed to provision container for agent %s: %s", agent.id, e)
        agent.status = AgentStatus.error

    await db.commit()
    await db.refresh(agent)
    return agent


async def start_agent(db: AsyncSession, agent: Agent) -> Agent:
    """Start a stopped agent's container."""
    if not agent.container_id:
        raise AgentProvisionError("Agent has no container")
    try:
        docker_manager.start_container(agent.container_id)
        agent.status = AgentStatus.running
    except Exception as e:
        logger.error("Failed to start container %s: %s", agent.container_id, e)
        agent.status = AgentStatus.error
    await db.commit()
    await db.refresh(agent)
    return agent


async def stop_agent(db: AsyncSession, agent: Agent) -> Agent:
    """Stop a running agent's container."""
    if agent.container_id:
        docker_manager.stop_container(agent.container_id)
    agent.status = AgentStatus.stopped
    await db.commit()
    await db.refresh(agent)
    return agent


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
        docker_manager.remove_container(agent.container_id)
    await db.delete(agent)
    await db.commit()
