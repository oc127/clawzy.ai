from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.credits import CreditTransaction, CreditReason

# Credits cost per 1K tokens — aligned with ARCHITECTURE.md
CREDIT_RATES: dict[str, dict[str, float]] = {
    "deepseek-chat":     {"input": 0.1,  "output": 0.2},
    "deepseek-reasoner": {"input": 0.4,  "output": 2.0},
    "qwen-turbo":        {"input": 0.05, "output": 0.1},
    "qwen-plus":         {"input": 0.1,  "output": 0.2},
    "qwen-max":          {"input": 0.3,  "output": 0.6},
    "claude-sonnet":     {"input": 2.0,  "output": 10.0},
    "claude-haiku":      {"input": 0.5,  "output": 1.5},
    "gpt-4o":            {"input": 1.5,  "output": 8.0},
    "gpt-4o-mini":       {"input": 0.1,  "output": 0.3},
    "gemini-flash":      {"input": 0.05, "output": 0.15},
}


class InsufficientCreditsError(Exception):
    pass


def calculate_credits(model_name: str, tokens_input: int, tokens_output: int) -> int:
    """Calculate credits cost for a model call."""
    rate = CREDIT_RATES.get(model_name, {"input": 1.0, "output": 2.0})
    cost = (tokens_input / 1000) * rate["input"] + (tokens_output / 1000) * rate["output"]
    return max(1, round(cost))


async def deduct_credits(
    db: AsyncSession,
    user_id: str,
    model_name: str,
    tokens_input: int,
    tokens_output: int,
    agent_id: str | None = None,
) -> int:
    """Deduct credits from user balance. Returns credits used."""
    credits_used = calculate_credits(model_name, tokens_input, tokens_output)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")
    if user.credit_balance < credits_used:
        raise InsufficientCreditsError()

    user.credit_balance -= credits_used

    txn = CreditTransaction(
        user_id=user_id,
        amount=-credits_used,
        balance_after=user.credit_balance,
        reason=CreditReason.usage,
        model_name=model_name,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        agent_id=agent_id,
    )
    db.add(txn)
    await db.commit()
    return credits_used


async def get_usage_this_period(db: AsyncSession, user_id: str) -> int:
    """Get total credits used in current billing period."""
    result = await db.execute(
        select(func.coalesce(func.sum(func.abs(CreditTransaction.amount)), 0)).where(
            CreditTransaction.user_id == user_id,
            CreditTransaction.reason == CreditReason.usage,
        )
    )
    return result.scalar_one()


async def get_usage_today(db: AsyncSession, user_id: str) -> int:
    """Get total credits used today (UTC)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.coalesce(func.sum(func.abs(CreditTransaction.amount)), 0)).where(
            CreditTransaction.user_id == user_id,
            CreditTransaction.reason == CreditReason.usage,
            CreditTransaction.created_at >= today_start,
        )
    )
    return result.scalar_one()


class DailyLimitExceededError(Exception):
    pass


async def check_daily_limit(db: AsyncSession, user: User) -> None:
    """Check if user has exceeded daily credit limit."""
    if user.daily_credit_limit is None:
        return
    used_today = await get_usage_today(db, user.id)
    if used_today >= user.daily_credit_limit:
        raise DailyLimitExceededError(
            f"Daily credit limit of {user.daily_credit_limit} reached. Used {used_today} today."
        )


async def get_usage_last_7_days(db: AsyncSession, user_id: str) -> list[dict]:
    """Get daily usage for the last 7 days."""
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            cast(CreditTransaction.created_at, Date).label("date"),
            func.coalesce(func.sum(func.abs(CreditTransaction.amount)), 0).label("credits"),
        )
        .where(
            CreditTransaction.user_id == user_id,
            CreditTransaction.reason == CreditReason.usage,
            CreditTransaction.created_at >= seven_days_ago,
        )
        .group_by(cast(CreditTransaction.created_at, Date))
        .order_by(cast(CreditTransaction.created_at, Date))
    )
    rows = result.all()
    usage_map = {str(row.date): int(row.credits) for row in rows}

    # Fill in missing days with 0
    days = []
    for i in range(7):
        day = (now - timedelta(days=6 - i)).date()
        days.append({"date": str(day), "credits": usage_map.get(str(day), 0)})
    return days
