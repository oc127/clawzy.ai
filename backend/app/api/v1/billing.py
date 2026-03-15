from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.credits import CreditTransaction, CreditReason
from app.models.subscription import Subscription, PlanType, SubStatus
from app.schemas.billing import (
    CreditsResponse,
    CreditTransactionResponse,
    PlanResponse,
    CheckoutRequest,
)
from app.services.agent_service import get_user_plan
from app.services.credits_service import get_usage_this_period, get_usage_today, get_usage_last_7_days

router = APIRouter(prefix="/billing", tags=["billing"])

PLANS = [
    PlanResponse(id="free", name="Free", price_monthly=0, credits_included=500, max_agents=1),
    PlanResponse(id="starter", name="Starter", price_monthly=9, credits_included=3000, max_agents=1),
    PlanResponse(id="pro", name="Pro", price_monthly=19, credits_included=8000, max_agents=3),
    PlanResponse(id="business", name="Business", price_monthly=39, credits_included=20000, max_agents=10),
]

PLAN_MAP = {p.id: p for p in PLANS}


@router.get("/credits", response_model=CreditsResponse)
async def get_credits(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_user_plan(db, user.id)
    used = await get_usage_this_period(db, user.id)
    return CreditsResponse(balance=user.credit_balance, used_this_period=used, plan=plan)


@router.get("/credits/transactions", response_model=list[CreditTransactionResponse])
async def get_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.get("/credits/today")
async def get_today_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    used = await get_usage_today(db, user.id)
    return {
        "used_today": used,
        "daily_limit": user.daily_credit_limit,
    }


@router.get("/credits/usage-chart")
async def get_usage_chart(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily usage for the last 7 days (for dashboard chart)."""
    return await get_usage_last_7_days(db, user.id)


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    return PLANS


@router.post("/subscribe")
async def subscribe_plan(
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Switch to a plan. Grants credits included in the plan."""
    target_plan = PLAN_MAP.get(body.plan)
    if not target_plan:
        raise HTTPException(status_code=400, detail="Invalid plan")

    current_plan = await get_user_plan(db, user.id)
    if current_plan == body.plan:
        raise HTTPException(status_code=400, detail="You are already on this plan")

    # Deactivate any existing active subscription
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status == SubStatus.active)
    )
    for sub in result.scalars().all():
        sub.status = SubStatus.canceled

    # Create new subscription
    now = datetime.now(timezone.utc)
    new_sub = Subscription(
        user_id=user.id,
        plan=PlanType(body.plan),
        status=SubStatus.active,
        current_period_start=now,
        credits_included=target_plan.credits_included,
    )
    db.add(new_sub)

    # Grant plan credits
    user.credit_balance += target_plan.credits_included
    tx = CreditTransaction(
        user_id=user.id,
        amount=target_plan.credits_included,
        balance_after=user.credit_balance,
        reason=CreditReason.subscription,
    )
    db.add(tx)

    await db.commit()

    return {"message": f"Switched to {target_plan.name} plan", "plan": body.plan}
