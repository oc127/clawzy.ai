import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.user import User
from app.models.credits import CreditTransaction, CreditReason
from app.services.agent_service import create_agent

logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


async def register_user(db: AsyncSession, email: str, password: str, name: str) -> tuple[User, str, str]:
    """Register a new user. Returns (user, access_token, refresh_token)."""
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise AuthError("Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        credit_balance=settings.signup_bonus_credits,
    )
    db.add(user)
    await db.flush()

    # Record signup bonus transaction
    txn = CreditTransaction(
        user_id=user.id,
        amount=settings.signup_bonus_credits,
        balance_after=settings.signup_bonus_credits,
        reason=CreditReason.signup_bonus,
    )
    db.add(txn)
    await db.commit()
    await db.refresh(user)

    # Auto-provision a default OpenClaw agent for the new user
    try:
        await create_agent(db, user.id, f"{name}'s Agent", "deepseek-chat")
        logger.info("Auto-provisioned OpenClaw agent for user %s", user.id)
    except Exception as e:
        logger.error("Failed to auto-provision agent for user %s: %s", user.id, e)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return user, access_token, refresh_token


async def login_user(db: AsyncSession, email: str, password: str) -> tuple[User, str, str]:
    """Authenticate user. Returns (user, access_token, refresh_token)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return user, access_token, refresh_token
