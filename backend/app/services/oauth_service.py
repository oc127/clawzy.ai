"""OAuth service — handles GitHub and Google OAuth2 login flows."""

import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.credits import CreditReason, CreditTransaction
from app.models.user import User

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


# --------------------------------------------------------------------------- #
#  GitHub OAuth
# --------------------------------------------------------------------------- #

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


def get_github_authorize_url(state: str) -> str:
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/v1/auth/github/callback"
    return (
        f"{GITHUB_AUTH_URL}"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=user:email"
        f"&state={state}"
    )


async def exchange_github_code(code: str) -> dict:
    """Exchange GitHub auth code for user info."""
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise OAuthError("Failed to get GitHub access token")

        # Get user profile
        headers = {"Authorization": f"Bearer {access_token}"}
        user_resp = await client.get(GITHUB_USER_URL, headers=headers)
        if user_resp.status_code != 200:
            raise OAuthError("Failed to get GitHub user info")
        user_data = user_resp.json()

        # Get primary email if not public
        email = user_data.get("email")
        if not email:
            emails_resp = await client.get(GITHUB_EMAILS_URL, headers=headers)
            if emails_resp.status_code == 200:
                for e in emails_resp.json():
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break

        if not email:
            raise OAuthError("No verified email found on GitHub account")

        return {
            "provider": "github",
            "provider_id": str(user_data["id"]),
            "email": email,
            "name": user_data.get("name") or user_data.get("login", ""),
            "avatar_url": user_data.get("avatar_url"),
        }


# --------------------------------------------------------------------------- #
#  Google OAuth
# --------------------------------------------------------------------------- #

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_authorize_url(state: str) -> str:
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/v1/auth/google/callback"
    return (
        f"{GOOGLE_AUTH_URL}"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid+email+profile"
        f"&state={state}"
        f"&access_type=offline"
    )


async def exchange_google_code(code: str) -> dict:
    """Exchange Google auth code for user info."""
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/v1/auth/google/callback"
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise OAuthError("Failed to get Google access token")

        user_resp = await client.get(
            GOOGLE_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise OAuthError("Failed to get Google user info")
        user_data = user_resp.json()

        email = user_data.get("email")
        if not email:
            raise OAuthError("No email found on Google account")

        return {
            "provider": "google",
            "provider_id": str(user_data["id"]),
            "email": email,
            "name": user_data.get("name", ""),
            "avatar_url": user_data.get("picture"),
        }


# --------------------------------------------------------------------------- #
#  Shared: find or create user from OAuth profile
# --------------------------------------------------------------------------- #


async def oauth_login_or_register(
    db: AsyncSession,
    provider: str,
    provider_id: str,
    email: str,
    name: str,
    avatar_url: str | None = None,
) -> tuple[User, str, str]:
    """Find existing user by OAuth provider+id or email, or create a new one.

    Returns (user, access_token, refresh_token).
    """
    # First, try to find by OAuth provider + provider_id
    result = await db.execute(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_provider_id == provider_id,
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Try to find by email (link accounts)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            # Link OAuth to existing account
            user.oauth_provider = provider
            user.oauth_provider_id = provider_id
            if not user.avatar_url and avatar_url:
                user.avatar_url = avatar_url

    if user is None:
        # Create new user
        user = User(
            email=email,
            name=name,
            avatar_url=avatar_url,
            oauth_provider=provider,
            oauth_provider_id=provider_id,
            credit_balance=settings.signup_bonus_credits,
        )
        db.add(user)
        await db.flush()

        # Record signup bonus
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
