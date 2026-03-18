import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthError, login_user, register_user

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


# --------------------------------------------------------------------------- #
#  OAuth providers info
# --------------------------------------------------------------------------- #


@router.get("/providers")
async def get_providers():
    """Return available OAuth providers (for frontend to show login buttons)."""
    providers = []
    if settings.github_client_id:
        providers.append({"id": "github", "name": "GitHub"})
    if settings.google_client_id:
        providers.append({"id": "google", "name": "Google"})
    return {"providers": providers}


# --------------------------------------------------------------------------- #
#  GitHub OAuth
# --------------------------------------------------------------------------- #


@router.get("/github/authorize")
async def github_authorize():
    """Redirect user to GitHub OAuth authorization page."""
    if not settings.github_client_id:
        raise HTTPException(status_code=501, detail="GitHub OAuth is not configured")

    from app.services.oauth_service import get_github_authorize_url

    state = secrets.token_urlsafe(32)
    url = get_github_authorize_url(state)
    return {"url": url, "state": state}


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback — exchange code for tokens."""
    if not settings.github_client_id:
        raise HTTPException(status_code=501, detail="GitHub OAuth is not configured")

    from app.services.oauth_service import OAuthError, exchange_github_code, oauth_login_or_register

    try:
        profile = await exchange_github_code(code)
        user, access_token, refresh_token = await oauth_login_or_register(
            db,
            provider=profile["provider"],
            provider_id=profile["provider_id"],
            email=profile["email"],
            name=profile["name"],
            avatar_url=profile.get("avatar_url"),
        )
    except OAuthError as e:
        # Redirect to login page with error
        params = urlencode({"error": e.detail})
        return RedirectResponse(url=f"/login?{params}")

    # Redirect to frontend with tokens in URL fragment (not query params for security)
    params = urlencode(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )
    return RedirectResponse(url=f"/auth/callback?{params}")


# --------------------------------------------------------------------------- #
#  Google OAuth
# --------------------------------------------------------------------------- #


@router.get("/google/authorize")
async def google_authorize():
    """Redirect user to Google OAuth authorization page."""
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")

    from app.services.oauth_service import get_google_authorize_url

    state = secrets.token_urlsafe(32)
    url = get_google_authorize_url(state)
    return {"url": url, "state": state}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback — exchange code for tokens."""
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")

    from app.services.oauth_service import OAuthError, exchange_google_code, oauth_login_or_register

    try:
        profile = await exchange_google_code(code)
        user, access_token, refresh_token = await oauth_login_or_register(
            db,
            provider=profile["provider"],
            provider_id=profile["provider_id"],
            email=profile["email"],
            name=profile["name"],
            avatar_url=profile.get("avatar_url"),
        )
    except OAuthError as e:
        params = urlencode({"error": e.detail})
        return RedirectResponse(url=f"/login?{params}")

    params = urlencode(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )
    return RedirectResponse(url=f"/auth/callback?{params}")
