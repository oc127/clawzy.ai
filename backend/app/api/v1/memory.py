"""Memory API — persistent cross-conversation memory management."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.memory_service import delete_memory, list_user_memories

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryResponse(BaseModel):
    id: str
    fact: str
    agent_id: str | None
    source_conversation_id: str | None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[MemoryResponse])
async def get_memories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    memories = await list_user_memories(db, user.id)
    return [
        MemoryResponse(
            id=m.id,
            fact=m.fact,
            agent_id=m.agent_id,
            source_conversation_id=m.source_conversation_id,
            created_at=m.created_at.isoformat(),
        )
        for m in memories
    ]


@router.delete("/{memory_id}")
async def remove_memory(
    memory_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_memory(db, memory_id, user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return {"ok": True}
