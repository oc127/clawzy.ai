from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.agent import Agent
from app.models.chat import Conversation, Message
from app.models.user import User

router = APIRouter(prefix="/backup", tags=["backup"])


@router.get("/export")
async def export_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export all user data (agents, conversations, messages) as JSON."""
    agents_result = await db.execute(
        select(Agent).where(Agent.user_id == user.id).order_by(Agent.created_at)
    )
    agents = list(agents_result.scalars().all())

    agents_data = []
    for agent in agents:
        convs_result = await db.execute(
            select(Conversation)
            .where(Conversation.agent_id == agent.id)
            .order_by(Conversation.created_at)
        )
        conversations = list(convs_result.scalars().all())

        convs_data = []
        for conv in conversations:
            msgs_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at)
            )
            messages = list(msgs_result.scalars().all())

            convs_data.append({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role.value,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                    }
                    for msg in messages
                ],
            })

        agents_data.append({
            "id": agent.id,
            "name": agent.name,
            "model_name": agent.model_name,
            "created_at": agent.created_at.isoformat(),
            "conversations": convs_data,
        })

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "agents": agents_data,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
