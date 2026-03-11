import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, create_access_token, create_refresh_token, TOKEN_EXPIRED
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.services.auth_service import register_user, login_user, AuthError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh = await register_user(db, body.email, body.password, body.name)
    except AuthError as e:
        logger.warning(
            "Registration failed: email=%s ip=%s reason=%s",
            body.email,
            request.client.host if request.client else "unknown",
            e.detail,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh = await login_user(db, body.email, body.password)
    except AuthError as e:
        logger.warning(
            "Login failed: email=%s ip=%s",
            body.email,
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload == TOKEN_EXPIRED:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    if not isinstance(payload, dict) or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload["sub"]

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )
