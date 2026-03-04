"""容器健康巡检 + 僵尸清理 + 基础设施深度检查 + 重启循环检测"""
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

import redis as sync_redis
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

# 同步 Redis（Celery 环境）
_redis = sync_redis.from_url(settings.redis_url)


def _send_alert_sync(title: str, message: str, severity: str = "warning") -> None:
    """同步发送告警（Celery 环境用）。"""
    try:
        from app.core.alerting import send_alert_sync
        send_alert_sync(title, message, severity)
    except Exception:
        logger.exception("Failed to send alert: %s", title)


@celery.task(name="app.workers.agent_tasks.check_all_agents")
def check_all_agents():
    """每 60 秒巡检所有 running Agent，带深度探测和重启循环检测。"""
    with Session(sync_engine) as db:
        agents = db.execute(
            select(Agent).where(Agent.status == AgentStatus.running)
        ).scalars().all()

        for agent in agents:
            if not agent.container_id:
                continue

            status = docker_manager.get_container_status(agent.container_id)

            if status is None or status == "exited":
                # 重启循环检测：10 分钟内重启 >3 次 → 标记 error + 告警
                restart_key = f"clawzy:restart_count:{agent.id}"
                restart_count = _redis.incr(restart_key)
                _redis.expire(restart_key, 600)  # 10 分钟窗口

                if restart_count > 3:
                    logger.error(
                        "Agent %s restart loop (%d restarts in 10min), marking as error",
                        agent.id, restart_count,
                    )
                    agent.status = AgentStatus.error
                    db.commit()
                    _send_alert_sync(
                        f"RESTART LOOP: Agent {agent.id}",
                        f"Container restarted {restart_count} times in 10 minutes. Marked as error.",
                        "critical",
                    )
                    continue

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
    """清理长期不活跃的容器：7 天停止，30 天删除。"""
    now = datetime.now(timezone.utc)

    with Session(sync_engine) as db:
        agents = db.execute(select(Agent)).scalars().all()

        for agent in agents:
            if not agent.last_active_at:
                continue

            inactive_days = (now - agent.last_active_at).days

            if inactive_days >= 30 and agent.container_id:
                logger.info(
                    "Removing zombie container for agent %s (inactive %d days)",
                    agent.id, inactive_days,
                )
                docker_manager.remove_container(agent.container_id, agent.id)
                agent.container_id = None
                agent.status = AgentStatus.stopped
                db.commit()

            elif inactive_days >= 7 and agent.status == AgentStatus.running and agent.container_id:
                logger.info(
                    "Stopping idle container for agent %s (inactive %d days)",
                    agent.id, inactive_days,
                )
                docker_manager.stop_container(agent.container_id)
                agent.status = AgentStatus.stopped
                db.commit()


@celery.task(name="app.workers.agent_tasks.infrastructure_health_check")
def infrastructure_health_check():
    """每 5 分钟：深度探测所有基础设施，存结果到 Redis，异常时告警。"""
    from app.services.health_service import run_all_health_checks, HealthStatus

    # Celery 心跳：写入当前时间戳，供 /health/deep 检查 Celery 是否存活
    import time
    try:
        _redis.set("clawzy:celery:heartbeat", str(time.time()), ex=900)
    except Exception:
        logger.warning("Failed to write Celery heartbeat to Redis")

    loop = asyncio.new_event_loop()
    try:
        results = loop.run_until_complete(run_all_health_checks())
    finally:
        loop.close()

    health_data = []
    for result in results:
        entry = {
            "service": result.service,
            "status": result.status.value,
            "latency_ms": round(result.latency_ms, 1),
            "details": result.details,
            "checked_at": result.checked_at,
        }
        health_data.append(entry)

        if result.status == HealthStatus.UNHEALTHY:
            _send_alert_sync(
                f"UNHEALTHY: {result.service}",
                f"Service {result.service} is unhealthy: {result.details}",
                "critical",
            )
        elif result.status == HealthStatus.DEGRADED:
            _send_alert_sync(
                f"DEGRADED: {result.service}",
                f"Service {result.service} is degraded: {result.details}",
                "warning",
            )

    _redis.set("clawzy:health:latest", json.dumps(health_data), ex=600)

    # Trigger Ops Agent analysis if any service is unhealthy
    unhealthy = [r for r in results if r.status == HealthStatus.UNHEALTHY]
    if unhealthy:
        event_desc = "\n".join(f"- {r.service}: {r.details}" for r in unhealthy)
        ops_agent_analyze.delay(event_desc)


@celery.task(name="app.workers.agent_tasks.ops_agent_analyze")
def ops_agent_analyze(event_description: str):
    """让运维 Agent 分析系统事件并决定行动。"""
    from app.services.ops_chat_service import ops_chat

    prompt = f"""系统自动检测到以下问题：

{event_description}

请：
1. 用 check_health 确认当前完整状态
2. 如果需要，查看相关服务日志
3. 判断是否需要立即处理
4. 如果需要重启或其他操作，执行对应工具
5. 通过 send_notification 向管理员报告你的分析和采取的行动"""

    loop = asyncio.new_event_loop()
    try:
        reply = loop.run_until_complete(ops_chat(prompt))
        logger.info("Ops Agent analysis: %s", reply[:200])
    except Exception:
        logger.exception("Ops Agent analysis failed")
    finally:
        loop.close()
