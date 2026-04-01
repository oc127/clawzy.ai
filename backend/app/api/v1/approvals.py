"""Approvals API — human-in-the-loop approval management."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.approval import ApprovalResolve, ApprovalResponse
from app.services.agent_service import get_agent
from app.services.approval_service import get_pending_approvals, resolve_approval

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/{agent_id}/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalResponse])
async def list_pending(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await get_pending_approvals(db, agent_id)


@router.post("/{approval_id}", response_model=ApprovalResponse)
async def resolve(
    agent_id: str,
    approval_id: str,
    body: ApprovalResolve,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    if body.decision not in ("approved", "denied"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approved' or 'denied'",
        )

    approval = await resolve_approval(db, approval_id, body.decision)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    return approval
