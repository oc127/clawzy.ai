import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.deps import get_current_user
from app.schemas.auth import (
    ChangePasswordRequest, ForgotPasswordRequest, LoginRequest, MessageResponse,
    RefreshRequest, RegisterRequest, ResetPasswordRequest, TokenResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import (
    AuthError, change_password, login_user, register_user,
    request_password_reset, resend_verification, reset_password, verify_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh = await register_user(db, body.email, body.password, body.name)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)
    except Exception:
        logger.exception("Unexpected error during registration")
        raise
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh = await login_user(db, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)
    except Exception:
        logger.exception("Unexpected error during login")
        raise
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await request_password_reset(db, body.email)
    # Always return success to prevent email enumeration
    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        await reset_password(db, body.token, body.new_password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    return MessageResponse(message="Password has been reset successfully.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password_endpoint(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await change_password(db, user, body.current_password, body.new_password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    return MessageResponse(message="Password changed successfully.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_endpoint(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    try:
        await verify_email(db, body.token)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    return MessageResponse(message="Email verified successfully.")


@router.post("/send-verification", response_model=MessageResponse)
async def send_verification(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await resend_verification(db, user)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    return MessageResponse(message="Verification email sent.")


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )
