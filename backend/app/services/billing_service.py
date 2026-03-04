"""Stripe 支付集成"""
import logging

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription, PlanType, SubStatus
from app.models.credits import CreditTransaction, CreditReason

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key

# Stripe Price ID → Plan 映射 (从 .env 读取实际 Price ID)
PRICE_TO_PLAN = {
    settings.stripe_price_starter: PlanType.starter,
    settings.stripe_price_pro: PlanType.pro,
    settings.stripe_price_business: PlanType.business,
}

PLAN_CREDITS = {
    PlanType.starter: 3000,
    PlanType.pro: 8000,
    PlanType.business: 20000,
}


async def create_checkout_session(db: AsyncSession, user: User, price_id: str) -> str:
    """创建 Stripe Checkout Session，返回 URL。"""
    # 确保用户有 Stripe customer
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, name=user.name)
        user.stripe_customer_id = customer.id
        await db.commit()

    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url="https://clawzy.ai/billing?success=true",
        cancel_url="https://clawzy.ai/billing?canceled=true",
        metadata={"user_id": user.id},
    )
    return session.url


async def create_portal_session(user: User) -> str:
    """创建 Stripe Customer Portal Session，用户可管理订阅。"""
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url="https://clawzy.ai/billing",
    )
    return session.url


async def handle_checkout_completed(db: AsyncSession, session_data: dict) -> None:
    """处理 checkout.session.completed 事件：创建订阅记录 + 充积分。"""
    user_id = session_data["metadata"]["user_id"]
    stripe_sub_id = session_data.get("subscription")

    if not stripe_sub_id:
        return

    stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)
    price_id = stripe_sub["items"]["data"][0]["price"]["id"]
    plan = PRICE_TO_PLAN.get(price_id, PlanType.starter)

    # 创建订阅记录
    sub = Subscription(
        user_id=user_id,
        plan=plan,
        stripe_subscription_id=stripe_sub_id,
        status=SubStatus.active,
        credits_included=PLAN_CREDITS.get(plan, 0),
    )
    db.add(sub)

    # 充入积分
    credits = PLAN_CREDITS.get(plan, 0)
    if credits > 0:
        user = await db.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if user:
            user.credit_balance += credits
            txn = CreditTransaction(
                user_id=user_id,
                amount=credits,
                balance_after=user.credit_balance,
                reason=CreditReason.subscription,
            )
            db.add(txn)

    await db.commit()
    logger.info("Subscription created: user=%s plan=%s credits=+%d", user_id, plan.value, credits)


async def handle_subscription_updated(db: AsyncSession, sub_data: dict) -> None:
    """处理订阅更新（升级/降级）。"""
    stripe_sub_id = sub_data["id"]
    status = sub_data["status"]

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    if status == "active":
        sub.status = SubStatus.active
    elif status == "past_due":
        sub.status = SubStatus.past_due
    elif status in ("canceled", "unpaid"):
        sub.status = SubStatus.canceled

    await db.commit()
    logger.info("Subscription updated: %s → %s", stripe_sub_id, status)


async def handle_subscription_deleted(db: AsyncSession, sub_data: dict) -> None:
    """处理订阅取消。"""
    stripe_sub_id = sub_data["id"]

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    sub.status = SubStatus.canceled
    await db.commit()
    logger.info("Subscription canceled: %s", stripe_sub_id)
