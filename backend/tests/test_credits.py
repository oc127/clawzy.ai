"""Unit tests for credits calculation and deduction logic."""

import pytest
import pytest_asyncio

from app.services.credits_service import (
    calculate_credits,
    deduct_credits,
    get_usage_this_period,
    InsufficientCreditsError,
    CREDIT_RATES,
)
from app.models.user import User
from app.models.credits import CreditTransaction, CreditReason


class TestCalculateCredits:
    def test_known_model_rates(self):
        # deepseek-chat: input=0.1, output=0.2
        # 1000 input + 1000 output = 0.1 + 0.2 = 0.3 → rounds to 0, min 1
        assert calculate_credits("deepseek-chat", 1000, 1000) == 1

    def test_large_usage(self):
        # deepseek-chat: 10000 input + 10000 output = 1.0 + 2.0 = 3.0
        assert calculate_credits("deepseek-chat", 10000, 10000) == 3

    def test_premium_model_is_expensive(self):
        # claude-sonnet: input=2.0, output=10.0
        # 5000 input + 5000 output = 10.0 + 50.0 = 60
        assert calculate_credits("claude-sonnet", 5000, 5000) == 60

    def test_unknown_model_uses_default_rates(self):
        # Unknown model uses default {input: 1.0, output: 2.0}
        # 1000 input + 1000 output = 1.0 + 2.0 = 3
        assert calculate_credits("unknown-model", 1000, 1000) == 3

    def test_zero_tokens_returns_minimum(self):
        assert calculate_credits("deepseek-chat", 0, 0) == 1

    def test_all_known_models_have_rates(self):
        expected = [
            "deepseek-chat", "deepseek-reasoner",
            "qwen-turbo", "qwen-plus", "qwen-max",
            "claude-sonnet", "claude-haiku",
            "gpt-4o", "gpt-4o-mini",
            "gemini-flash",
        ]
        for model in expected:
            assert model in CREDIT_RATES


@pytest.mark.asyncio
class TestDeductCredits:
    async def test_successful_deduction(self, db, test_user):
        credits_used = await deduct_credits(
            db, test_user.id, "deepseek-chat", 5000, 5000
        )
        assert credits_used >= 1
        await db.refresh(test_user)
        assert test_user.credit_balance == 500 - credits_used

    async def test_creates_transaction_record(self, db, test_user):
        await deduct_credits(db, test_user.id, "deepseek-chat", 1000, 1000)
        from sqlalchemy import select
        result = await db.execute(
            select(CreditTransaction).where(
                CreditTransaction.user_id == test_user.id,
                CreditTransaction.reason == CreditReason.usage,
            )
        )
        txn = result.scalar_one()
        assert txn.amount < 0
        assert txn.model_name == "deepseek-chat"

    async def test_insufficient_credits_raises(self, db, test_user):
        # Use a premium model with massive tokens to exceed 500 credits
        with pytest.raises(InsufficientCreditsError):
            await deduct_credits(
                db, test_user.id, "claude-sonnet", 100000, 100000
            )

    async def test_user_not_found_raises(self, db):
        with pytest.raises(ValueError, match="User not found"):
            await deduct_credits(db, "nonexistent-id", "deepseek-chat", 100, 100)


@pytest.mark.asyncio
class TestGetUsageThisPeriod:
    async def test_returns_zero_for_new_user(self, db, test_user):
        usage = await get_usage_this_period(db, test_user.id)
        assert usage == 0

    async def test_tracks_usage(self, db, test_user):
        await deduct_credits(db, test_user.id, "deepseek-chat", 5000, 5000)
        usage = await get_usage_this_period(db, test_user.id)
        assert usage >= 1
