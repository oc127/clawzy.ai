import json
import logging

import httpx
import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.deps import get_current_user
from app.models.credits import CreditReason, CreditTransaction
from app.models.subscription import PlanType, SubStatus, Subscription
from app.models.user import User
from app.schemas.billing import (
    CheckoutRequest,
    CreditsResponse,
    CreditTransactionResponse,
    PlanResponse,
)
from app.services.agent_service import get_user_plan
from app.services.credits_service import get_usage_this_period

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

PLANS = [
    PlanResponse(id="free", name="Free", price_monthly=0, credits_included=500, max_agents=1),
    PlanResponse(id="starter", name="Starter", price_monthly=9, credits_included=3000, max_agents=1),
    PlanResponse(id="pro", name="Pro", price_monthly=19, credits_included=8000, max_agents=3),
    PlanResponse(id="business", name="Business", price_monthly=39, credits_included=20000, max_agents=10),
]

# Map Stripe plan IDs to credits
PLAN_CREDITS: dict[str, int] = {
    "starter": 3000,
    "pro": 8000,
    "business": 20000,
}

# Map Apple product IDs to credits (mirrors StoreKitManager.swift allCreditPlans)
APPLE_PRODUCT_CREDITS: dict[str, int] = {
    "ai.clawzy.app.sub.4k":   4_000,
    "ai.clawzy.app.sub.8k":   8_000,
    "ai.clawzy.app.sub.12k":  12_000,
    "ai.clawzy.app.sub.16k":  16_000,
    "ai.clawzy.app.sub.20k":  20_000,
    "ai.clawzy.app.sub.40k":  40_000,
    "ai.clawzy.app.sub.63k":  63_000,
    "ai.clawzy.app.sub.85k":  85_000,
    "ai.clawzy.app.sub.110k": 110_000,
    "ai.clawzy.app.sub.170k": 170_000,
    "ai.clawzy.app.sub.230k": 230_000,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _add_credits(
    db: AsyncSession,
    user: User,
    amount: int,
    reason: CreditReason,
    description: str = "",
) -> None:
    user.credit_balance += amount
    txn = CreditTransaction(
        user_id=user.id,
        amount=amount,
        balance_after=user.credit_balance,
        reason=reason,
    )
    db.add(txn)
    await db.commit()
    logger.info("Added %d credits to user %s (%s)", amount, user.id, description)


# ---------------------------------------------------------------------------
# Standard endpoints
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Stripe webhook
# ---------------------------------------------------------------------------

@router.post("/stripe/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive and process Stripe webhook events."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as exc:
        logger.error("Stripe webhook parse error: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data)
    elif event_type == "invoice.paid":
        await _handle_invoice_paid(db, data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data)
    else:
        logger.debug("Unhandled Stripe event type: %s", event_type)

    return {"received": True}


async def _resolve_user_by_stripe_customer(
    db: AsyncSession, customer_id: str
) -> User | None:
    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    return result.scalar_one_or_none()


async def _handle_checkout_completed(db: AsyncSession, session: dict) -> None:
    """checkout.session.completed — grant credits after successful payment."""
    customer_id = session.get("customer")
    metadata = session.get("metadata", {})
    user_id = metadata.get("user_id")

    user: User | None = None
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    elif customer_id:
        user = await _resolve_user_by_stripe_customer(db, customer_id)

    if user is None:
        logger.warning("checkout.session.completed: user not found (customer=%s)", customer_id)
        return

    # Persist Stripe customer ID if not already set
    if customer_id and not user.stripe_customer_id:
        user.stripe_customer_id = customer_id

    plan_id = metadata.get("plan", "")
    credits = PLAN_CREDITS.get(plan_id, int(metadata.get("credits", 0)))
    if credits <= 0:
        logger.warning("checkout.session.completed: no credits for plan=%s", plan_id)
        return

    await _add_credits(db, user, credits, CreditReason.topup, f"stripe checkout plan={plan_id}")

    # Update or create subscription record
    stripe_sub_id = session.get("subscription")
    if stripe_sub_id and plan_id:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        sub = result.scalar_one_or_none()
        plan_enum = PlanType[plan_id] if plan_id in PlanType.__members__ else PlanType.free
        if sub:
            sub.plan = plan_enum
            sub.stripe_subscription_id = stripe_sub_id
            sub.status = SubStatus.active
            sub.credits_included = credits
        else:
            db.add(Subscription(
                user_id=user.id,
                plan=plan_enum,
                stripe_subscription_id=stripe_sub_id,
                status=SubStatus.active,
                credits_included=credits,
            ))
        await db.commit()


async def _handle_invoice_paid(db: AsyncSession, invoice: dict) -> None:
    """invoice.paid — subscription renewed, grant monthly credits."""
    customer_id = invoice.get("customer")
    if not customer_id:
        return

    user = await _resolve_user_by_stripe_customer(db, customer_id)
    if user is None:
        logger.warning("invoice.paid: user not found (customer=%s)", customer_id)
        return

    # Find subscription to know credit amount
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()
    credits = sub.credits_included if sub else 0

    if credits <= 0:
        logger.warning("invoice.paid: no credits_included for user=%s", user.id)
        return

    await _add_credits(db, user, credits, CreditReason.subscription, "stripe invoice.paid renewal")


async def _handle_subscription_deleted(db: AsyncSession, subscription: dict) -> None:
    """customer.subscription.deleted — mark subscription canceled."""
    stripe_sub_id = subscription.get("id")
    if not stripe_sub_id:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        logger.warning("subscription.deleted: subscription not found id=%s", stripe_sub_id)
        return

    sub.status = SubStatus.canceled
    sub.plan = PlanType.free
    await db.commit()
    logger.info("Subscription canceled for user=%s (stripe_sub=%s)", sub.user_id, stripe_sub_id)


# ---------------------------------------------------------------------------
# Apple StoreKit receipt verification
# ---------------------------------------------------------------------------

APPLE_VERIFY_URL_PROD = "https://buy.itunes.apple.com/verifyReceipt"
APPLE_VERIFY_URL_SANDBOX = "https://sandbox.itunes.apple.com/verifyReceipt"


@router.post("/apple-receipt", status_code=status.HTTP_200_OK)
async def verify_apple_receipt(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive an iOS App Store receipt, verify with Apple, and credit the user.

    Expected JSON body:
      { "receipt_data": "<base64-encoded receipt>", "transaction_id": "<optional>" }
    """
    body = await request.json()
    receipt_data: str = body.get("receipt_data", "")
    if not receipt_data:
        raise HTTPException(status_code=422, detail="receipt_data is required")

    if not settings.apple_shared_secret:
        raise HTTPException(status_code=500, detail="Apple shared secret not configured")

    verify_payload = {
        "receipt-data": receipt_data,
        "password": settings.apple_shared_secret,
        "exclude-old-transactions": True,
    }

    verified_receipt = await _call_apple_verify(verify_payload)
    if verified_receipt is None:
        raise HTTPException(status_code=400, detail="Receipt verification failed")

    status_code_apple = verified_receipt.get("status", -1)
    if status_code_apple != 0:
        raise HTTPException(
            status_code=400,
            detail=f"Apple verification returned status {status_code_apple}",
        )

    # Extract latest receipts (prefer latest_receipt_info for auto-renewable subs)
    latest_receipts: list[dict] = verified_receipt.get("latest_receipt_info") or []
    if not latest_receipts:
        latest_receipts = verified_receipt.get("receipt", {}).get("in_app", [])

    if not latest_receipts:
        raise HTTPException(status_code=400, detail="No purchases found in receipt")

    # Deduplicate by product_id — pick the most recent transaction per product
    seen_products: set[str] = set()
    total_credits = 0
    granted_products: list[str] = []

    for item in sorted(latest_receipts, key=lambda x: x.get("purchase_date_ms", "0"), reverse=True):
        product_id = item.get("product_id", "")
        if product_id in seen_products:
            continue
        seen_products.add(product_id)

        credits = APPLE_PRODUCT_CREDITS.get(product_id, 0)
        if credits > 0:
            total_credits += credits
            granted_products.append(product_id)

    if total_credits <= 0:
        raise HTTPException(status_code=400, detail="No recognized products in receipt")

    await _add_credits(
        db, user, total_credits, CreditReason.subscription,
        f"apple receipt products={','.join(granted_products)}"
    )

    return {
        "credits_granted": total_credits,
        "products": granted_products,
        "balance": user.credit_balance,
    }


async def _call_apple_verify(payload: dict) -> dict | None:
    """Call Apple's verifyReceipt endpoint; retry sandbox on status 21007."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(APPLE_VERIFY_URL_PROD, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("Apple verify (prod) failed: %s", exc)
            return None

        # status 21007 means receipt is from sandbox — retry against sandbox
        if data.get("status") == 21007:
            try:
                resp = await client.post(APPLE_VERIFY_URL_SANDBOX, json=payload)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                logger.error("Apple verify (sandbox) failed: %s", exc)
                return None

    return data
