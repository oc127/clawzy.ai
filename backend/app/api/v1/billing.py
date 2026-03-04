import logging

import stripe
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.credits import CreditTransaction
from app.schemas.billing import CreditsResponse, CreditTransactionResponse, PlanResponse
from app.services.agent_service import get_user_plan
from app.services.credits_service import get_usage_this_period
from app.services import billing_service

logger = logging.getLogger(__name__)

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


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    return PLANS


@router.post("/checkout")
async def create_checkout(
    price_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建 Stripe Checkout Session，返回支付页面 URL。"""
    url = await billing_service.create_checkout_session(db, user, price_id)
    return {"url": url}


@router.post("/portal")
async def create_portal(user: User = Depends(get_current_user)):
    """创建 Stripe Customer Portal，用户管理订阅。"""
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription")
    url = await billing_service.create_portal_session(user)
    return {"url": url}


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """处理 Stripe Webhook 回调。"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await billing_service.handle_checkout_completed(db, data)
    elif event_type == "customer.subscription.updated":
        await billing_service.handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        await billing_service.handle_subscription_deleted(db, data)
    else:
        logger.debug("Unhandled Stripe event: %s", event_type)

    return {"status": "ok"}
