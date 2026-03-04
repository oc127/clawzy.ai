"""定时计费任务"""
import logging

from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription, SubStatus
from app.models.credits import CreditTransaction, CreditReason
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)

sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace(
    "postgresql+psycopg2", "postgresql"
)
sync_engine = create_engine(sync_db_url)

# 每档套餐每月赠送的积分（累加到现有余额，不重置）
PLAN_CREDITS = {
    "starter": 3000,
    "pro": 8000,
    "business": 20000,
}


@celery.task(name="app.workers.billing_tasks.add_monthly_subscription_credits")
def add_monthly_subscription_credits():
    """每月 1 号给付费用户累加积分（不重置，上月剩余自动累计）。"""
    with Session(sync_engine) as db:
        subs = db.execute(
            select(Subscription).where(Subscription.status == SubStatus.active)
        ).scalars().all()

        for sub in subs:
            credits_to_add = PLAN_CREDITS.get(sub.plan.value, 0)
            if credits_to_add <= 0:
                continue

            user = db.execute(
                select(User).where(User.id == sub.user_id)
            ).scalar_one_or_none()
            if not user:
                continue

            user.credit_balance += credits_to_add

            txn = CreditTransaction(
                user_id=user.id,
                amount=credits_to_add,
                balance_after=user.credit_balance,
                reason=CreditReason.subscription,
            )
            db.add(txn)
            db.commit()

            logger.info(
                "Added monthly credits for user %s: +%d (plan=%s, new_balance=%d)",
                user.id, credits_to_add, sub.plan.value, user.credit_balance,
            )
