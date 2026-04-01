"""Approval service — human-in-the-loop approval via Redis pub/sub."""

import asyncio
import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.approval import ApprovalRequest

logger = logging.getLogger(__name__)

# Redis channel prefix for approval pub/sub
_APPROVAL_CHANNEL = "clawzy:approvals"


def _get_redis():
    """Create an async Redis client."""
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def request_approval(
    db: AsyncSession,
    agent_id: str,
    user_id: str,
    tool_name: str,
    tool_args: dict | None = None,
    conversation_id: str | None = None,
) -> ApprovalRequest:
    """Create a pending approval request and publish to Redis."""
    approval = ApprovalRequest(
        agent_id=agent_id,
        user_id=user_id,
        tool_name=tool_name,
        tool_args=tool_args,
        status="pending",
        conversation_id=conversation_id,
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)

    # Publish notification to Redis
    try:
        r = _get_redis()
        await r.publish(
            f"{_APPROVAL_CHANNEL}:{agent_id}",
            json.dumps({
                "type": "approval_requested",
                "approval_id": approval.id,
                "tool_name": tool_name,
                "tool_args": tool_args,
            }),
        )
        await r.aclose()
    except Exception as exc:
        logger.warning("Failed to publish approval request to Redis: %s", exc)

    logger.info(
        "Approval requested: id=%s agent=%s tool=%s",
        approval.id, agent_id, tool_name,
    )
    return approval


async def resolve_approval(
    db: AsyncSession,
    approval_id: str,
    decision: str,
) -> ApprovalRequest | None:
    """Approve or deny an approval request and publish result to Redis."""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        return None

    if approval.status != "pending":
        return approval  # Already resolved

    approval.status = decision  # 'approved' or 'denied'
    approval.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(approval)

    # Publish resolution to Redis for waiting consumers
    try:
        r = _get_redis()
        await r.publish(
            f"{_APPROVAL_CHANNEL}:result:{approval_id}",
            json.dumps({
                "type": "approval_resolved",
                "approval_id": approval.id,
                "decision": decision,
            }),
        )
        await r.aclose()
    except Exception as exc:
        logger.warning("Failed to publish approval resolution to Redis: %s", exc)

    logger.info("Approval %s resolved: %s", approval_id, decision)
    return approval


async def wait_for_approval(approval_id: str, timeout: int = 300) -> str | None:
    """
    Async wait for an approval decision via Redis pub/sub.

    Returns 'approved', 'denied', or None if timeout.
    """
    r = _get_redis()
    pubsub = r.pubsub()
    channel = f"{_APPROVAL_CHANNEL}:result:{approval_id}"

    try:
        await pubsub.subscribe(channel)

        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            msg = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                timeout=min(remaining, 5.0),
            )
            if msg and msg.get("type") == "message":
                try:
                    data = json.loads(msg["data"])
                    return data.get("decision")
                except (json.JSONDecodeError, TypeError):
                    pass

    except asyncio.TimeoutError:
        pass
    except Exception as exc:
        logger.error("Error waiting for approval %s: %s", approval_id, exc)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await r.aclose()

    return None


async def get_pending_approvals(
    db: AsyncSession, agent_id: str
) -> list[ApprovalRequest]:
    """Get all pending approval requests for an agent."""
    result = await db.execute(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.agent_id == agent_id,
            ApprovalRequest.status == "pending",
        )
        .order_by(ApprovalRequest.created_at.desc())
    )
    return list(result.scalars().all())
