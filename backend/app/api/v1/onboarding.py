"""Lucy onboarding endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.onboarding_service import setup_lucy_onboarding, generate_lucy_greeting

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingRequest(BaseModel):
    user_name: str | None = None


class OnboardingResponse(BaseModel):
    agent_id: str
    agent_name: str
    greeting: str


class GreetingResponse(BaseModel):
    greeting: str


@router.post("/lucy", response_model=OnboardingResponse)
async def lucy_onboarding(
    body: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initialize Lucy for a new user — creates default agent and returns greeting."""
    result = await setup_lucy_onboarding(db, str(current_user.id), body.user_name)
    return OnboardingResponse(**result)


@router.get("/lucy/greeting", response_model=GreetingResponse)
async def lucy_greeting(
    user_name: str | None = None,
):
    """Get Lucy's greeting message (no auth required for preview)."""
    greeting = await generate_lucy_greeting(user_name)
    return GreetingResponse(greeting=greeting)
