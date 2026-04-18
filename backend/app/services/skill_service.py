"""Skill service — manage agent skills (SKILL.md-based prompt injection)."""

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import AgentSkill

logger = logging.getLogger(__name__)

# Maximum skills to inject per request (keeps prompt short)
_MAX_INJECTED_SKILLS = 3

_EXTRACT_PROMPT = """You are a skill extraction system. Analyze the following conversation and determine if it contains a reusable pattern, workflow, or specialized knowledge that could help an AI agent handle similar requests in the future.

Conversation:
{conversation}

If you identify a clear, reusable pattern, respond with a JSON object:
{{
  "found": true,
  "name": "Short skill name (max 50 chars)",
  "description": "One sentence describing what this skill does",
  "triggers": ["keyword1", "keyword2", "keyword3"],
  "content": "Markdown instructions for how to handle this type of task. Be specific and actionable."
}}

If there is no clear reusable pattern (e.g., simple Q&A, one-off task), respond with:
{{"found": false}}

Rules:
- Only extract skills for non-trivial, repeatable patterns
- triggers should be 2-5 short keywords that would appear in future similar requests
- content should be a SKILL.md-style instruction block (200 words max)
- Do NOT extract skills from casual conversation or simple factual questions"""


async def _call_llm(prompt: str) -> str:
    """Make a non-streaming LLM call via shared LiteLLM client."""
    from app.core.http_client import get_litellm_client

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.3,
    }
    client = get_litellm_client()
    resp = await client.post("/v1/chat/completions", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "auto-skill"


async def install_skill(
    db: AsyncSession,
    agent_id: str,
    slug: str,
    name: str,
    source: str,
    content: str | None = None,
    description: str | None = None,
    triggers: list[str] | None = None,
) -> AgentSkill:
    """Install a skill on an agent."""
    skill = AgentSkill(
        agent_id=agent_id,
        slug=slug,
        name=name,
        description=description,
        triggers=triggers,
        source=source,
        skill_content=content,
        enabled=True,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    logger.info("Installed skill '%s' on agent %s (source=%s)", slug, agent_id, source)
    return skill


async def update_skill(
    db: AsyncSession,
    skill_id: str,
    name: str | None = None,
    description: str | None = None,
    triggers: list[str] | None = None,
    content: str | None = None,
    enabled: bool | None = None,
) -> AgentSkill | None:
    """Update skill fields."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return None
    if name is not None:
        skill.name = name
    if description is not None:
        skill.description = description
    if triggers is not None:
        skill.triggers = triggers
    if content is not None:
        skill.skill_content = content
        skill.version = (skill.version or 1) + 1
    if enabled is not None:
        skill.enabled = enabled
    skill.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(skill)
    return skill


async def find_relevant_skills(
    db: AsyncSession,
    agent_id: str,
    user_message: str,
) -> list[AgentSkill]:
    """Match enabled skills by trigger keywords in user message.

    Returns up to _MAX_INJECTED_SKILLS skills ranked by number of trigger hits.
    """
    result = await db.execute(
        select(AgentSkill)
        .where(AgentSkill.agent_id == agent_id, AgentSkill.enabled.is_(True))
        .order_by(AgentSkill.usage_count.desc())
    )
    skills = list(result.scalars().all())

    if not skills:
        return []

    msg_lower = user_message.lower()
    scored: list[tuple[int, AgentSkill]] = []
    for skill in skills:
        if not skill.triggers:
            continue
        hits = sum(1 for t in skill.triggers if t.lower() in msg_lower)
        if hits > 0:
            scored.append((hits, skill))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:_MAX_INJECTED_SKILLS]]


async def inject_skills_to_prompt(
    db: AsyncSession,
    agent_id: str,
    user_message: str,
    system_prompt: str,
) -> str:
    """Inject relevant skills into the system prompt.

    1. Always prepend a compact built-in skills index so the agent knows
       what's available (progressive disclosure).
    2. When user message triggers a match, inject the full skill content for
       both built-in (disk) and custom (DB) skills — up to _MAX_INJECTED_SKILLS
       total, preferring the highest-scoring matches.
    """
    from app.services.skill_loader import (
        match_skills as match_builtin_skills,
        get_skill as get_builtin_skill,
        build_skills_index_prompt,
    )

    # ── a. Compact built-in skills index (always injected) ─────────────────
    skills_index = build_skills_index_prompt()

    # ── b. Match built-in skills by trigger keywords ────────────────────────
    builtin_matches = match_builtin_skills(user_message, max_results=_MAX_INJECTED_SKILLS)

    # ── c. Match custom DB skills by trigger keywords ────────────────────────
    db_matched = await find_relevant_skills(db, agent_id, user_message)

    # ── d. Merge and deduplicate (builtin first, then DB) ───────────────────
    combined_sections: list[str] = []
    injected_count = 0

    for bmeta in builtin_matches:
        if injected_count >= _MAX_INJECTED_SKILLS:
            break
        full = get_builtin_skill(bmeta.name)
        if full:
            combined_sections.append(f"### {full.name}")
            combined_sections.append(f"_{full.description}_\n")
            combined_sections.append(full.content)
            combined_sections.append("")
            injected_count += 1

    for skill in db_matched:
        if injected_count >= _MAX_INJECTED_SKILLS:
            break
        combined_sections.append(f"### {skill.name}")
        if skill.description:
            combined_sections.append(f"_{skill.description}_\n")
        if skill.skill_content:
            combined_sections.append(skill.skill_content)
        combined_sections.append("")
        skill.usage_count = (skill.usage_count or 0) + 1
        injected_count += 1

    if db_matched:
        await db.commit()

    # ── e. Build final prompt ────────────────────────────────────────────────
    parts: list[str] = []
    if system_prompt:
        parts.append(system_prompt)

    if skills_index:
        parts.append(skills_index)

    if combined_sections:
        parts.append("## Active Skills (loaded)\n")
        parts.extend(combined_sections)

    return "\n\n".join(parts) if parts else system_prompt


async def auto_extract_skill(
    db: AsyncSession,
    agent_id: str,
    conversation_messages: list[dict],
) -> AgentSkill | None:
    """Use LLM to detect and create a reusable skill from a conversation.

    Designed to run as a fire-and-forget background task.
    """
    if not conversation_messages:
        return None

    # Format conversation for the prompt
    lines = []
    for msg in conversation_messages[-10:]:  # last 10 messages max
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            lines.append(f"{role.upper()}: {content[:500]}")

    if not lines:
        return None

    conversation_text = "\n".join(lines)

    try:
        raw = await _call_llm(_EXTRACT_PROMPT.format(conversation=conversation_text))

        # Strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        data = json.loads(cleaned)
        if not isinstance(data, dict) or not data.get("found"):
            return None

        name = data.get("name", "Auto Skill")[:50]
        description = data.get("description", "")
        triggers = data.get("triggers", [])
        content = data.get("content", "")

        if not content:
            return None

        slug = f"auto-{_slugify(name)}-{uuid.uuid4().hex[:6]}"
        skill = await install_skill(
            db,
            agent_id=agent_id,
            slug=slug,
            name=name,
            source="auto",
            content=content,
            description=description,
            triggers=triggers[:5],  # cap at 5 triggers
        )
        logger.info("Auto-extracted skill '%s' for agent %s", name, agent_id)
        return skill

    except Exception as exc:
        logger.warning("Skill auto-extraction failed for agent %s: %s", agent_id, exc)
        return None


async def update_skill_stats(
    db: AsyncSession,
    skill_id: str,
    success: bool,
) -> None:
    """Update usage count and rolling success rate for a skill."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return
    count = (skill.usage_count or 0) + 1
    # Rolling average: new_rate = (old_rate * old_count + outcome) / new_count
    old_rate = skill.success_rate if skill.success_rate is not None else 1.0
    old_count = skill.usage_count or 0
    new_rate = (old_rate * old_count + (1.0 if success else 0.0)) / count
    skill.usage_count = count
    skill.success_rate = round(new_rate, 4)
    skill.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def get_enabled_skills(db: AsyncSession, agent_id: str) -> list[AgentSkill]:
    """Return all enabled skills for an agent (for prompt injection)."""
    result = await db.execute(
        select(AgentSkill)
        .where(AgentSkill.agent_id == agent_id, AgentSkill.enabled.is_(True))
        .order_by(AgentSkill.installed_at)
    )
    return list(result.scalars().all())


def build_skill_prompt(skills: list[AgentSkill]) -> str:
    """Format enabled skills into a system prompt section."""
    if not skills:
        return ""

    sections = ["## Active Skills\n"]
    for skill in skills:
        sections.append(f"### {skill.name} ({skill.slug})")
        if skill.skill_content:
            sections.append(skill.skill_content)
        sections.append("")
    return "\n".join(sections)


async def list_skills(db: AsyncSession, agent_id: str) -> list[AgentSkill]:
    """List all skills for an agent (enabled and disabled)."""
    result = await db.execute(
        select(AgentSkill)
        .where(AgentSkill.agent_id == agent_id)
        .order_by(AgentSkill.installed_at.desc())
    )
    return list(result.scalars().all())


async def get_skill(db: AsyncSession, skill_id: str) -> AgentSkill | None:
    """Get a single skill by ID."""
    result = await db.execute(
        select(AgentSkill).where(AgentSkill.id == skill_id)
    )
    return result.scalar_one_or_none()


async def toggle_skill(db: AsyncSession, skill_id: str, enabled: bool) -> AgentSkill | None:
    """Enable or disable a skill."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return None
    skill.enabled = enabled
    skill.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(skill)
    return skill


async def delete_skill(db: AsyncSession, skill_id: str) -> bool:
    """Remove a skill."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return False
    await db.delete(skill)
    await db.commit()
    return True
