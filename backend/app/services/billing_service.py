"""Stripe 支付集成"""
import logging
from datetime import datetime, timezone

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

# Plan → max agents 限制
PLAN_MAX_AGENTS = {
    PlanType.free: 1,
    PlanType.starter: 1,
    PlanType.pro: 3,
    PlanType.business: 10,
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
        success_url=f"{settings.app_url}/billing?success=true",
        cancel_url=f"{settings.app_url}/billing?canceled=true",
        metadata={"user_id": str(user.id)},
    )
    return session.url


async def create_portal_session(user: User) -> str:
    """创建 Stripe Customer Portal Session，用户可管理订阅。"""
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.app_url}/billing",
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
    """处理订阅更新（升级/降级/状态变化）。"""
    stripe_sub_id = sub_data["id"]
    status = sub_data["status"]

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    old_status = sub.status

    if status == "active":
        sub.status = SubStatus.active
        # 同步账单周期
        if sub_data.get("current_period_start"):
            sub.current_period_start = datetime.fromtimestamp(
                sub_data["current_period_start"], tz=timezone.utc
            )
        if sub_data.get("current_period_end"):
            sub.current_period_end = datetime.fromtimestamp(
                sub_data["current_period_end"], tz=timezone.utc
            )
        # 检测升降级：price 变了
        new_price_id = sub_data.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
        if new_price_id:
            new_plan = PRICE_TO_PLAN.get(new_price_id)
            if new_plan and new_plan != sub.plan:
                old_plan = sub.plan
                sub.plan = new_plan
                sub.credits_included = PLAN_CREDITS.get(new_plan, 0)
                logger.info("Plan changed: %s → %s for sub %s", old_plan.value, new_plan.value, stripe_sub_id)
    elif status == "past_due":
        sub.status = SubStatus.past_due
    elif status in ("canceled", "unpaid"):
        sub.status = SubStatus.canceled

    await db.commit()
    logger.info("Subscription updated: %s → %s (was %s)", stripe_sub_id, status, old_status.value)


async def handle_subscription_deleted(db: AsyncSession, sub_data: dict) -> None:
    """处理订阅取消：标记 canceled + 降级为 free + 停止多余容器。"""
    from app.services.agent_service import list_agents, stop_agent

    stripe_sub_id = sub_data["id"]

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    sub.status = SubStatus.canceled
    user_id = sub.user_id

    # 查找用户
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    # 停止超出 free plan 上限的 agent（free = 1 个）
    free_max = PLAN_MAX_AGENTS[PlanType.free]
    agents = await list_agents(db, user_id)
    running_agents = [a for a in agents if a.status.value == "running"]

    stopped_count = 0
    for agent in running_agents[free_max:]:
        try:
            await stop_agent(db, agent)
            stopped_count += 1
        except Exception:
            logger.warning("Failed to stop agent %s during downgrade", agent.id)

    await db.commit()

    # 发送退订通知邮件
    if user:
        _send_subscription_canceled_email(user.email, sub.plan.value)

    logger.info(
        "Subscription canceled: %s (user=%s, stopped %d agents)",
        stripe_sub_id, user_id, stopped_count,
    )


async def handle_invoice_payment_failed(db: AsyncSession, invoice_data: dict) -> None:
    """处理支付失败：标记 past_due + 发通知邮件。

    Stripe 自动 retry（Smart Retries），我们只负责通知用户 + 更新状态。
    """
    stripe_sub_id = invoice_data.get("subscription")
    if not stripe_sub_id:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    sub.status = SubStatus.past_due
    await db.commit()

    # 查找用户发邮件
    user_result = await db.execute(select(User).where(User.id == sub.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        attempt_count = invoice_data.get("attempt_count", 1)
        amount_due = invoice_data.get("amount_due", 0) / 100  # cents → dollars
        _send_payment_failed_email(user.email, sub.plan.value, attempt_count, amount_due)

    logger.warning(
        "Payment failed: sub=%s user=%s attempt=%d",
        stripe_sub_id, sub.user_id, invoice_data.get("attempt_count", 1),
    )


async def handle_invoice_paid(db: AsyncSession, invoice_data: dict) -> None:
    """处理续费成功（非首次）：给用户充月度积分。

    首次支付已由 checkout.session.completed 处理，
    这里只处理 billing_reason = subscription_cycle 的续费。
    """
    billing_reason = invoice_data.get("billing_reason")
    if billing_reason != "subscription_cycle":
        return

    stripe_sub_id = invoice_data.get("subscription")
    if not stripe_sub_id:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub or sub.status != SubStatus.active:
        return

    credits = PLAN_CREDITS.get(sub.plan, 0)
    if credits <= 0:
        return

    user_result = await db.execute(
        select(User).where(User.id == sub.user_id).with_for_update()
    )
    user = user_result.scalar_one_or_none()
    if not user:
        return

    user.credit_balance += credits
    txn = CreditTransaction(
        user_id=user.id,
        amount=credits,
        balance_after=user.credit_balance,
        reason=CreditReason.subscription,
    )
    db.add(txn)

    # 如果之前是 past_due，现在付款成功了，恢复 active
    if sub.status == SubStatus.past_due:
        sub.status = SubStatus.active

    await db.commit()
    logger.info("Invoice paid (renewal): user=%s plan=%s credits=+%d", user.id, sub.plan.value, credits)


# ---------------------------------------------------------------------------
# 邮件通知 helpers
# ---------------------------------------------------------------------------

def _send_payment_failed_email(to: str, plan: str, attempt: int, amount: float) -> None:
    """支付失败通知邮件。"""
    from app.core.email import send_email, _wrap_email

    content = f"""
    <h2 style="color:#1a1a2e;font-size:20px;margin:0 0 16px;">Payment Failed</h2>
    <p style="color:#4a4a68;font-size:15px;line-height:1.6;margin:0 0 16px;">
      We were unable to process your payment of <strong>${amount:.2f}</strong>
      for your <strong>{plan.title()}</strong> plan (attempt {attempt}).
    </p>
    <p style="color:#4a4a68;font-size:15px;line-height:1.6;margin:0 0 24px;">
      Please update your payment method to avoid service interruption.
      We'll automatically retry in a few days.
    </p>
    <p style="text-align:center;margin:0 0 24px;">
      <a href="{settings.app_url}/billing"
         style="display:inline-block;padding:14px 32px;background:#dc2626;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;font-size:15px;">
        Update Payment Method
      </a>
    </p>
    <p style="color:#999;font-size:13px;margin:0;">
      If this is resolved, you can ignore this email.
    </p>
    """
    send_email(to, "Clawzy.ai — Payment Failed", _wrap_email(content))


def _send_subscription_canceled_email(to: str, plan: str) -> None:
    """退订确认邮件。"""
    from app.core.email import send_email, _wrap_email

    content = f"""
    <h2 style="color:#1a1a2e;font-size:20px;margin:0 0 16px;">Subscription Canceled</h2>
    <p style="color:#4a4a68;font-size:15px;line-height:1.6;margin:0 0 16px;">
      Your <strong>{plan.title()}</strong> subscription has been canceled.
      Your account has been downgraded to the Free plan.
    </p>
    <p style="color:#4a4a68;font-size:15px;line-height:1.6;margin:0 0 24px;">
      Your remaining energy balance is still available.
      You can resubscribe anytime to get more energy and features.
    </p>
    <p style="text-align:center;margin:0 0 24px;">
      <a href="{settings.app_url}/billing"
         style="display:inline-block;padding:14px 32px;background:#2563eb;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;font-size:15px;">
        Resubscribe
      </a>
    </p>
    """
    send_email(to, "Clawzy.ai — Subscription Canceled", _wrap_email(content))
