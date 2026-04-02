from sqlalchemy import select, func, update, text
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
    """Deduct credits from user balance atomically. Returns credits used."""
    credits_used = calculate_credits(model_name, tokens_input, tokens_output)

    # Atomic UPDATE: only succeeds if balance >= credits_used (no race condition)
    result = await db.execute(
        update(User)
        .where(User.id == user_id, User.credit_balance >= credits_used)
        .values(credit_balance=User.credit_balance - credits_used)
        .returning(User.credit_balance)
    )
    row = result.first()
    if row is None:
        # Either user not found or insufficient balance
        check = await db.execute(select(User.credit_balance).where(User.id == user_id))
        user_row = check.first()
        if user_row is None:
            raise ValueError("User not found")
        raise InsufficientCreditsError()

    new_balance = row[0]

    txn = CreditTransaction(
        user_id=user_id,
        amount=-credits_used,
        balance_after=new_balance,
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
