import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import (
    decode_token, create_access_token, create_refresh_token,
    hash_password, verify_password,
)
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest,
    ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest,
)
from app.models.user import User
from app.services.auth_service import register_user, login_user, AuthError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh = await register_user(db, body.email, body.password, body.name)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)

    # Send verification email (async, non-blocking)
    try:
        token = secrets.token_urlsafe(32)
        r = await get_redis()
        await r.set(f"clawzy:email_verify:{token}", user.id, ex=86400)  # 24h
        from app.core.email import send_verification_email
        send_verification_email(user.email, token)
    except Exception:
        logger.warning("Failed to send verification email to %s", user.email)

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh = await login_user(db, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload["sub"]
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send password reset email. Always returns 200 (to prevent email enumeration)."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        token = secrets.token_urlsafe(32)
        r = await get_redis()
        await r.set(f"clawzy:pwd_reset:{token}", user.id, ex=1800)  # 30 min
        from app.core.email import send_password_reset_email
        send_password_reset_email(user.email, token)

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token from email."""
    r = await get_redis()
    user_id = await r.get(f"clawzy:pwd_reset:{body.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = user_id.decode() if isinstance(user_id, bytes) else user_id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    await db.commit()

    # Invalidate the token
    await r.delete(f"clawzy:pwd_reset:{body.token}")

    return {"message": "Password has been reset"}


@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify email using token from email."""
    r = await get_redis()
    user_id = await r.get(f"clawzy:email_verify:{body.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user_id = user_id.decode() if isinstance(user_id, bytes) else user_id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.email_verified = True
    await db.commit()

    await r.delete(f"clawzy:email_verify:{body.token}")

    return {"message": "Email verified"}


@router.post("/resend-verification")
async def resend_verification(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Resend verification email."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user and not user.email_verified:
        token = secrets.token_urlsafe(32)
        r = await get_redis()
        await r.set(f"clawzy:email_verify:{token}", user.id, ex=86400)
        from app.core.email import send_verification_email
        send_verification_email(user.email, token)

    return {"message": "If the email exists and is not verified, a verification link has been sent"}
