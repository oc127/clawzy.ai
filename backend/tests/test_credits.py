"""Tests for credits calculation, deduction, and insufficient balance."""

import uuid
import pytest
import pytest_asyncio

from app.models.user import User
from app.core.security import hash_password
from app.services.credits_service import (
    calculate_credits,
    deduct_credits,
    get_usage_this_period,
    InsufficientCreditsError,
)


@pytest_asyncio.fixture
async def credits_user(db_session):
    """Create a test user with 500 credits."""
    user = User(
        email=f"credits-test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("testpass123"),
        name="Credits Test",
        credit_balance=500,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestCalculateCredits:
    def test_known_model(self):
        """deepseek-chat: 0.1/1k input + 0.2/1k output → small cost."""
        cost = calculate_credits("deepseek-chat", 1000, 1000)
        # 0.1 + 0.2 = 0.3 → rounds to 1 (min 1)
        assert cost >= 1

    def test_expensive_model(self):
        """claude-sonnet: 2.0/1k input + 10.0/1k output → higher cost."""
        cost = calculate_credits("claude-sonnet", 1000, 1000)
        # 2.0 + 10.0 = 12.0 → 12
        assert cost == 12

    def test_unknown_model_uses_default(self):
        """Unknown model uses fallback rate 1.0/2.0."""
        cost = calculate_credits("unknown-model", 1000, 1000)
        # 1.0 + 2.0 = 3.0 → 3
        assert cost == 3

    def test_minimum_cost_is_one(self):
        """Even tiny usage should cost at least 1 credit."""
        cost = calculate_credits("deepseek-chat", 1, 1)
        assert cost == 1

    def test_large_usage(self):
        """Large token counts should scale proportionally."""
        small = calculate_credits("deepseek-chat", 1000, 1000)
        large = calculate_credits("deepseek-chat", 10000, 10000)
        assert large > small


@pytest.mark.asyncio
class TestDeductCredits:
    async def test_successful_deduction(self, db_session, credits_user):
        """Credits should decrease after deduction."""
        initial = credits_user.credit_balance
        used = await deduct_credits(
            db_session, credits_user.id, "deepseek-chat", 1000, 1000
        )
        assert used >= 1
        await db_session.refresh(credits_user)
        assert credits_user.credit_balance == initial - used

    async def test_transaction_created(self, db_session, credits_user):
        """Deduction should create a CreditTransaction record."""
        from sqlalchemy import select
        from app.models.credits import CreditTransaction

        await deduct_credits(
            db_session, credits_user.id, "deepseek-chat", 1000, 1000
        )

        result = await db_session.execute(
            select(CreditTransaction).where(
                CreditTransaction.user_id == credits_user.id
            )
        )
        txns = list(result.scalars().all())
        assert len(txns) >= 1
        assert txns[-1].amount < 0  # debit
        assert txns[-1].model_name == "deepseek-chat"

    async def test_insufficient_credits(self, db_session, credits_user):
        """Should raise InsufficientCreditsError when balance is too low."""
        credits_user.credit_balance = 0
        await db_session.commit()

        with pytest.raises(InsufficientCreditsError):
            await deduct_credits(
                db_session, credits_user.id, "claude-sonnet", 10000, 10000
            )

    async def test_deduction_with_agent_id(self, db_session, credits_user):
        """agent_id should be stored in the transaction."""
        from sqlalchemy import select
        from app.models.credits import CreditTransaction

        await deduct_credits(
            db_session, credits_user.id, "deepseek-chat", 1000, 1000,
            agent_id="test-agent-id"
        )

        result = await db_session.execute(
            select(CreditTransaction).where(
                CreditTransaction.agent_id == "test-agent-id"
            )
        )
        txn = result.scalar_one_or_none()
        assert txn is not None


@pytest.mark.asyncio
async def test_get_usage_this_period(db_session, credits_user):
    """Usage tracking should sum absolute deduction amounts."""
    await deduct_credits(db_session, credits_user.id, "deepseek-chat", 1000, 1000)
    await deduct_credits(db_session, credits_user.id, "deepseek-chat", 1000, 1000)

    usage = await get_usage_this_period(db_session, credits_user.id)
    assert usage >= 2  # At least 2 credits used (1 min per deduction)
