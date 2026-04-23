"""Improvement service — evaluate conversations, extract patterns, improve agent skills."""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Conversation, Message
from app.models.evaluation import ConversationEvaluation

logger = logging.getLogger(__name__)

_EVAL_PROMPT = """Evaluate this AI conversation. Return a JSON object with these exact fields:
{{
  "score": <0.0-1.0 overall quality>,
  "relevance_score": <0.0-1.0>,
  "coherence_score": <0.0-1.0>,
  "helpfulness_score": <0.0-1.0>,
  "summary": "<one sentence summary>",
  "patterns_found": ["<pattern1>", "<pattern2>"],
  "improvement_suggestions": ["<suggestion1>", "<suggestion2>"]
}}

Conversation:
{conversation}"""


async def _call_llm(prompt: str) -> str:
    import httpx
    from app.config import settings

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.litellm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 512,
                },
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("LLM call failed: %s", e)
        return "{}"


async def evaluate_response(conversation_id: str, user_id: str, agent_id: str | None, db: AsyncSession) -> ConversationEvaluation:
    """Evaluate a single conversation and store the result."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(50)
    )
    messages = result.scalars().all()

    if not messages:
        raise ValueError(f"Conversation {conversation_id} has no messages")

    convo_text = "\n".join(
        f"{m.role.upper()}: {m.content[:500]}" for m in messages
    )
    prompt = _EVAL_PROMPT.format(conversation=convo_text)
    raw = await _call_llm(prompt)

    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    evaluation = ConversationEvaluation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        score=data.get("score"),
        relevance_score=data.get("relevance_score"),
        coherence_score=data.get("coherence_score"),
        helpfulness_score=data.get("helpfulness_score"),
        summary=data.get("summary"),
        patterns_found=data.get("patterns_found", []),
        improvement_suggestions=data.get("improvement_suggestions", []),
        skill_extracted=False,
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


async def extract_patterns(user_id: str, db: AsyncSession, limit: int = 20) -> list[dict]:
    """Extract patterns from recent evaluations."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(ConversationEvaluation)
        .where(
            ConversationEvaluation.user_id == user_id,
            ConversationEvaluation.created_at >= cutoff,
        )
        .order_by(ConversationEvaluation.created_at.desc())
        .limit(limit)
    )
    evals = result.scalars().all()

    all_patterns: list[str] = []
    for ev in evals:
        if ev.patterns_found:
            all_patterns.extend(ev.patterns_found)

    seen: set[str] = set()
    unique_patterns = [p for p in all_patterns if not (p in seen or seen.add(p))]
    return [{"pattern": p} for p in unique_patterns[:20]]


async def improve_skills(user_id: str, agent_id: str | None, db: AsyncSession, max_conversations: int = 20) -> dict:
    """Run skill improvement cycle based on recent evaluations."""
    from app.services.skill_service import auto_extract_skill

    filters = [
        ConversationEvaluation.user_id == user_id,
        ConversationEvaluation.skill_extracted == False,
    ]
    if agent_id:
        filters.append(ConversationEvaluation.agent_id == agent_id)

    result = await db.execute(
        select(ConversationEvaluation)
        .where(*filters)
        .order_by(ConversationEvaluation.created_at.desc())
        .limit(max_conversations)
    )
    evals = result.scalars().all()

    skills_created = 0
    for ev in evals:
        if not ev.conversation_id or not ev.patterns_found:
            ev.skill_extracted = True
            continue

        target_agent_id = agent_id or ev.agent_id
        if target_agent_id:
            msgs_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == ev.conversation_id)
                .order_by(Message.created_at)
                .limit(30)
            )
            messages = msgs_result.scalars().all()
            if messages:
                convo_dicts = [{"role": m.role, "content": m.content} for m in messages]
                try:
                    skill = await auto_extract_skill(
                        db=db,
                        agent_id=target_agent_id,
                        conversation_messages=convo_dicts,
                    )
                    if skill:
                        skills_created += 1
                except Exception as e:
                    logger.warning("Skill extraction failed: %s", e)

        ev.skill_extracted = True

    await db.commit()
    return {"evaluations_processed": len(evals), "skills_created": skills_created}


async def generate_improvement_report(user_id: str, db: AsyncSession, period_days: int = 7) -> dict:
    """Generate a summary improvement report for a user."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    result = await db.execute(
        select(ConversationEvaluation)
        .where(
            ConversationEvaluation.user_id == user_id,
            ConversationEvaluation.created_at >= cutoff,
        )
    )
    evals = result.scalars().all()

    if not evals:
        return {
            "user_id": user_id,
            "period_days": period_days,
            "total_evaluations": 0,
            "avg_score": None,
            "top_patterns": [],
            "skills_extracted": 0,
            "recommendations": ["Start chatting with your agents to generate evaluation data."],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    scores = [e.score for e in evals if e.score is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    all_patterns: list[str] = []
    for ev in evals:
        if ev.patterns_found:
            all_patterns.extend(ev.patterns_found)

    seen: set[str] = set()
    top_patterns = [p for p in all_patterns if not (p in seen or seen.add(p))][:5]

    skills_extracted = sum(1 for e in evals if e.skill_extracted)

    recommendations: list[str] = []
    if avg_score is not None and avg_score < 0.6:
        recommendations.append("Response quality is below average. Consider refining agent system prompts.")
    if skills_extracted == 0:
        recommendations.append("No skills extracted yet. Use POST /improvement/improve to trigger extraction.")
    if len(evals) < 5:
        recommendations.append("Evaluate more conversations to get meaningful insights.")
    if not recommendations:
        recommendations.append("Agent performance looks good. Keep monitoring regularly.")

    return {
        "user_id": user_id,
        "period_days": period_days,
        "total_evaluations": len(evals),
        "avg_score": round(avg_score, 3) if avg_score else None,
        "top_patterns": top_patterns,
        "skills_extracted": skills_extracted,
        "recommendations": recommendations,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_improvement_cycle(user_id: str, agent_id: str | None, db: AsyncSession) -> dict:
    """Full improvement cycle: extract patterns → improve skills → report."""
    patterns = await extract_patterns(user_id, db)
    improvement = await improve_skills(user_id, agent_id, db)
    report = await generate_improvement_report(user_id, db)

    return {
        "patterns_extracted": len(patterns),
        "skills_created": improvement["skills_created"],
        "evaluations_processed": improvement["evaluations_processed"],
        "report_summary": report,
    }
