from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.credits import CreditTransaction
from app.schemas.billing import CreditsResponse, CreditTransactionResponse, PlanResponse
from app.services.agent_service import get_user_plan
from app.services.credits_service import get_usage_this_period

router = APIRouter(prefix="/billing", tags=["billing"])

PLANS = [
    PlanResponse(id="free", name="Free", price_monthly=0, credits_included=500, max_agents=1),
    PlanResponse(id="starter", name="Starter", price_monthly=9, credits_included=3000, max_agents=1),
    PlanResponse(id="pro", name="Pro", price_monthly=19, credits_included=8000, max_agents=3),
    PlanResponse(id="business", name="Business", price_monthly=39, credits_included=20000, max_agents=10),
]


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
    limit: int = Query(default=50, ge=1, le=100),
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


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    return PLANS
