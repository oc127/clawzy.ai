from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.credits import CreditReason, CreditTransaction
from app.models.user import User


class AuthError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


async def register_user(db: AsyncSession, email: str, password: str, name: str) -> tuple[User, str, str]:
    """Register a new user. Returns (user, access_token, refresh_token)."""
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing is not None:
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

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return user, access_token, refresh_token


async def login_user(db: AsyncSession, email: str, password: str) -> tuple[User, str, str]:
    """Authenticate user. Returns (user, access_token, refresh_token)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("Invalid email or password")

    # OAuth-only users cannot login with password
    if user.password_hash is None:
        provider = user.oauth_provider or "OAuth"
        raise AuthError(f"This account uses {provider} login. Please sign in with {provider}.")

    if not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return user, access_token, refresh_token
