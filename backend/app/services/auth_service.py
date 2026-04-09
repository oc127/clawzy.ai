import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.credits import CreditReason, CreditTransaction
from app.models.user import User
from app.services.email_service import send_password_reset_email


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


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Generate a reset token and send an email. Always succeeds (no email leak)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return  # Don't reveal whether the email exists

    token = secrets.token_urlsafe(48)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(UTC) + timedelta(
        minutes=settings.password_reset_expire_minutes
    )
    await db.commit()

    await send_password_reset_email(email, token)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> User:
    """Validate the reset token and update the user's password."""
    result = await db.execute(
        select(User).where(User.password_reset_token == token)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("Invalid or expired reset token")
    if user.password_reset_expires is None or user.password_reset_expires < datetime.now(UTC):
        raise AuthError("Invalid or expired reset token")

    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(db: AsyncSession, user: User, current_password: str, new_password: str) -> User:
    """Change password for an authenticated user."""
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Current password is incorrect")
    user.password_hash = hash_password(new_password)
    await db.commit()
    await db.refresh(user)
    return user
