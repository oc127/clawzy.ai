import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.character import CharacterTemplate
from app.models.user import User
from app.schemas.character import AgentFromCharacterResponse, CharacterCreate, CharacterResponse
from app.services.agent_service import AgentLimitError, create_agent, start_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("", response_model=list[CharacterResponse])
async def list_characters(db: AsyncSession = Depends(get_db)):
    """Public — returns all preset + UGC characters ordered by usage."""
    result = await db.execute(
        select(CharacterTemplate).order_by(
            CharacterTemplate.is_preset.desc(),
            CharacterTemplate.usage_count.desc(),
            CharacterTemplate.created_at.asc(),
        )
    )
    return list(result.scalars().all())


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CharacterTemplate).where(CharacterTemplate.id == character_id)
    )
    char = result.scalar_one_or_none()
    if char is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return char


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    body: CharacterCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom (UGC) character."""
    char = CharacterTemplate(
        name=body.name,
        name_reading=body.name_reading,
        age=body.age,
        occupation=body.occupation,
        personality_type=body.personality_type,
        personality_traits=body.personality_traits,
        speaking_style=body.speaking_style,
        catchphrase=body.catchphrase,
        interests=body.interests,
        backstory=body.backstory,
        system_prompt=body.system_prompt,
        greeting_message=body.greeting_message,
        sample_dialogues=body.sample_dialogues,
        avatar_color=body.avatar_color,
        category=body.category,
        is_preset=False,
        creator_id=user.id,
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)
    return char


@router.post("/{character_id}/use", response_model=AgentFromCharacterResponse, status_code=status.HTTP_201_CREATED)
async def use_character(
    character_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create and start an Agent from a character template."""
    result = await db.execute(
        select(CharacterTemplate).where(CharacterTemplate.id == character_id)
    )
    char = result.scalar_one_or_none()
    if char is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    try:
        agent = await create_agent(db, user.id, char.name, "deepseek-chat", char.system_prompt)
    except AgentLimitError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    try:
        agent = await start_agent(db, agent)
    except Exception as exc:
        logger.warning("Auto-start failed for character agent %s: %s", agent.id, exc)

    char.usage_count += 1
    await db.commit()

    return AgentFromCharacterResponse(
        agent_id=agent.id,
        character_id=char.id,
        character_name=char.name,
    )
