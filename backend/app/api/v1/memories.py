"""Memories API — manage agent long-term memory."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.agent_service import get_agent
from app.services.memory_service import list_memories, delete_memory, synthesize_daily

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/memories", tags=["memories"])


@router.get("")
async def list_agent_memories(
    agent_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List memories for an agent (paginated)."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    memories = await list_memories(db, agent_id, offset=offset, limit=limit)
    return {
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "memory_type": m.memory_type,
                "importance": m.importance,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ],
        "offset": offset,
        "limit": limit,
    }


@router.post("/synthesize")
async def synthesize_agent_memories(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger memory synthesis — compress daily facts into long-term summaries."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    result = await synthesize_daily(db, agent_id)
    if result is None:
        return {"status": "skipped", "message": "Not enough memories to synthesize"}
    return {"status": "synthesized", "memory_id": result.id}


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_memory(
    agent_id: str,
    memory_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific memory."""
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    deleted = await delete_memory(db, memory_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
