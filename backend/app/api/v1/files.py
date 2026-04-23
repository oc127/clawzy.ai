"""Files API — manage agent file records."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.agent_file import AgentFile
from app.models.user import User
from app.schemas.agent_file import AgentFileCreate, AgentFileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[AgentFileResponse])
async def list_files(
    agent_id: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(AgentFile).where(AgentFile.user_id == user.id)
    if agent_id:
        q = q.where(AgentFile.agent_id == agent_id)
    q = q.order_by(AgentFile.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=AgentFileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    body: AgentFileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = AgentFile(user_id=user.id, **body.model_dump())
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


@router.get("/{file_id}", response_model=AgentFileResponse)
async def get_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentFile).where(AgentFile.id == file_id, AgentFile.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentFile).where(AgentFile.id == file_id, AgentFile.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    await db.delete(file)
    await db.commit()
