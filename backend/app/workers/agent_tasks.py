"""容器健康巡检 + 僵尸容器清理"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.core.docker_manager import docker_manager
from app.models.agent import Agent, AgentStatus
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)

# Celery 任务用同步引擎（Celery worker 不是 asyncio 环境）
sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace(
    "postgresql+psycopg2", "postgresql"
)
sync_engine = create_engine(sync_db_url)


@celery.task(name="app.workers.agent_tasks.check_all_agents")
def check_all_agents():
    """每 60 秒巡检所有 status='running' 的 Agent，确认容器还活着。"""
    with Session(sync_engine) as db:
        agents = db.execute(
            select(Agent).where(Agent.status == AgentStatus.running)
        ).scalars().all()

        for agent in agents:
            if not agent.container_id:
                continue

            status = docker_manager.get_container_status(agent.container_id)

            if status is None or status == "exited":
                logger.warning(
                    "Agent %s container %s is down (status=%s), restarting...",
                    agent.id, agent.container_id, status,
                )
                try:
                    docker_manager.start_container(agent.container_id)
                    logger.info("Agent %s container restarted", agent.id)
                except Exception:
                    logger.exception("Failed to restart agent %s, marking as error", agent.id)
                    agent.status = AgentStatus.error
                    db.commit()

            elif status == "running":
                agent.last_active_at = datetime.now(timezone.utc)
                db.commit()


@celery.task(name="app.workers.agent_tasks.cleanup_zombie_containers")
def cleanup_zombie_containers():
    """清理长期不活跃的容器：Free 用户 7 天停止，30 天删除。"""
    now = datetime.now(timezone.utc)

    with Session(sync_engine) as db:
        agents = db.execute(select(Agent)).scalars().all()

        for agent in agents:
            if not agent.last_active_at:
                continue

            inactive_days = (now - agent.last_active_at).days

            # 超过 30 天不活跃 → 删除容器
            if inactive_days >= 30 and agent.container_id:
                logger.info(
                    "Removing zombie container for agent %s (inactive %d days)",
                    agent.id, inactive_days,
                )
                docker_manager.remove_container(agent.container_id)
                agent.container_id = None
                agent.status = AgentStatus.stopped
                db.commit()

            # 超过 7 天不活跃 → 停止容器
            elif inactive_days >= 7 and agent.status == AgentStatus.running and agent.container_id:
                logger.info(
                    "Stopping idle container for agent %s (inactive %d days)",
                    agent.id, inactive_days,
                )
                docker_manager.stop_container(agent.container_id)
                agent.status = AgentStatus.stopped
                db.commit()
