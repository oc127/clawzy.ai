from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "clawzy",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery.conf.beat_schedule = {
    # 每 60 秒巡检所有容器健康状态
    "agent-health-check": {
        "task": "app.workers.agent_tasks.check_all_agents",
        "schedule": 60.0,
    },
    # 每天凌晨 3:00 清理僵尸容器
    "cleanup-zombie-containers": {
        "task": "app.workers.agent_tasks.cleanup_zombie_containers",
        "schedule": crontab(hour=3, minute=0),
    },
    # 每月 1 号重置订阅用户积分
    "monthly-credit-reset": {
        "task": "app.workers.billing_tasks.reset_subscription_credits",
        "schedule": crontab(day_of_month=1, hour=0, minute=5),
    },
}

celery.autodiscover_tasks(["app.workers"])
