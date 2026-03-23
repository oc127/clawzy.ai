from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.template import AgentTemplate

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    category: str
    model_name: str
    system_prompt: str
    sort_order: int

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    """Public endpoint — returns all active ClawHub templates."""
    result = await db.execute(
        select(AgentTemplate)
        .where(AgentTemplate.is_active == True)  # noqa: E712
        .order_by(AgentTemplate.sort_order.asc(), AgentTemplate.created_at.asc())
    )
    return list(result.scalars().all())
