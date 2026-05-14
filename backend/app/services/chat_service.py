"""Chat service — streams LLM responses for Lucy companion and manages conversations."""

import json
import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chat import Conversation, Message, MessageRole
from app.models.lucy_state import LucyState
from app.services.credits_service import InsufficientCreditsError, deduct_credits
from app.services.cultural_engine import CulturalFrame, detect_cultural_frame
from app.services.epistemic_engine import assess_confidence, calibrate_response
from app.services.existential_memory import get_lucy_narrative
from app.services.memory_service import extract_memories, get_relevant_memories
from app.services.model_router import route as model_route
from app.services.safety_guard import SafetyGuard
from app.services.smart_router import smart_route
from app.services.soul_engine import (
    analyze_mood,
    build_system_prompt,
    calculate_affection_delta,
    get_unlockable_expressions,
)
from app.services.symbiotic_evolution import get_evolution_context
from app.services.transparency_engine import (
    assess_user_level,
    detect_task_type,
    get_transparency_instructions,
)

logger = logging.getLogger(__name__)

# Fixed identifier used as agent_id placeholder in conversations for Lucy.
LUCY_AGENT_ID = "lucy"


async def get_or_create_conversation(
    db: AsyncSession, agent_id: str, conversation_id: str | None = None
) -> Conversation:
    """Get existing conversation or create a new one.

    ``agent_id`` is kept in the signature for backward compatibility with the
    Conversation model; callers should pass ``LUCY_AGENT_ID``.
    """
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.agent_id == agent_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    conv = Conversation(agent_id=agent_id)
    db.add(conv)
    await db.flush()
    return conv


async def save_message(
    db: AsyncSession,
    conversation_id: str,
    role: MessageRole,
    content: str,
    model_name: str | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    credits_used: int | None = None,
) -> Message:
    """Persist a message to the database."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model_name=model_name,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        credits_used=credits_used,
    )
    db.add(msg)
    await db.flush()
    return msg


async def get_conversation_history(db: AsyncSession, conversation_id: str, limit: int = 20) -> list[dict]:
    """Get recent messages for context."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": m.role.value, "content": m.content} for m in messages]


async def _fetch_skill_prompts(db: AsyncSession, lucy_state: LucyState) -> list[str]:
    """Query enabled skill prompt templates for the user's Lucy instance.

    We reuse the AgentSkill join table with ``LUCY_AGENT_ID`` as a placeholder.
    If no rows match the fixed identifier we fall back to an empty list.
    """
    from app.models.skill import AgentSkill as AgentSkillModel, Skill as SkillModel

    result = await db.execute(
        select(SkillModel.prompt_template)
        .join(AgentSkillModel, AgentSkillModel.skill_id == SkillModel.id)
        .where(
            AgentSkillModel.agent_id == LUCY_AGENT_ID,
            AgentSkillModel.enabled == True,  # noqa: E712
            SkillModel.prompt_template.isnot(None),
        )
    )
    return [row[0] for row in result.all() if row[0]]


async def stream_chat_completion(
    db: AsyncSession,
    user_id: str,
    lucy_state: LucyState,
    conversation_id: str,
    user_content: str,
):
    """
    Stream a chat completion for Lucy.

    Yields JSON-encoded event dicts:
      {"type": "stream", "content": "..."}
      {"type": "done", "usage": {"credits": N, "balance": M}, "conversation_id": "..."}
      {"type": "error", "code": "...", "message": "..."}
    """
    # ── Safety Guard setup ──
    guard = SafetyGuard()
    guard.start_turn()

    # Save user message
    await save_message(db, conversation_id, MessageRole.user, user_content)
    await db.commit()

    # Build message history for context
    history = await get_conversation_history(db, conversation_id)

    # ── Soul Engine: build system prompt ──
    memories = await get_relevant_memories(db, user_id)
    skill_prompts = await _fetch_skill_prompts(db, lucy_state)
    lucy_experiences = await get_lucy_narrative(db, user_id, limit=5)
    evolution_ctx = await get_evolution_context(db, user_id)

    # ── Cultural Frame Switching: detect and apply cultural cognitive framework ──
    try:
        cached_frame = getattr(lucy_state, "cultural_frame", None)
        if cached_frame and cached_frame != "universal":
            cultural_frame = CulturalFrame(cached_frame)
        else:
            cultural_frame = await detect_cultural_frame(
                messages=history,
                user_language=None,
                user_memories=memories,
            )
            # Cache the detected frame on the state to avoid re-detection
            if hasattr(lucy_state, "cultural_frame"):
                lucy_state.cultural_frame = cultural_frame.value
    except Exception:
        logger.debug("Cultural frame detection skipped", exc_info=True)
        cultural_frame = None

    system_prompt = build_system_prompt(
        lucy_state, memories, skill_prompts,
        lucy_experiences=lucy_experiences or None,
        evolution_context=evolution_ctx or None,
        cultural_frame=cultural_frame,
    )

    # ── Adaptive Transparency: assess user level & inject instructions ──
    try:
        user_level = await assess_user_level(history, memories)
        lucy_state.user_level = user_level.value

        task_type = detect_task_type(user_content)
        transparency_instructions = get_transparency_instructions(user_level, task_type)
        system_prompt += f"\n\n[Communication style]\n{transparency_instructions}"
    except Exception:
        logger.debug("Transparency assessment skipped", exc_info=True)

    # Append concise instruction from Safety Guard when token budget is running low
    concise_instruction = guard.token_budget.get_concise_instruction()
    if concise_instruction:
        system_prompt += f"\n\n{concise_instruction}"

    # ── Knowledge Base RAG: inject relevant context from user's knowledge bases ──
    try:
        from app.services import knowledge_service

        kb_context = await knowledge_service.get_relevant_context(
            db, user_id, user_content, max_tokens=2000
        )
        if kb_context:
            system_prompt += (
                f"\n\n[Knowledge Base Context]\n{kb_context}\n\n"
                "Use this information to answer accurately."
            )
    except Exception:
        logger.debug("Knowledge base context injection skipped", exc_info=True)

    # Prepend the assembled system prompt to the message history
    history.insert(0, {"role": "system", "content": system_prompt})

    # ── Morphogenic Fluidity: intelligent model routing based on task nature ──
    try:
        route_config = await model_route(
            message=user_content,
            conversation_context=history,
            user_preferred_model=lucy_state.preferred_model,
        )
        effective_model = route_config["model"]
        cognitive_mode = route_config.get("cognitive_mode", "conversational")
        was_downgraded = effective_model != lucy_state.preferred_model
    except Exception:
        logger.debug("Model router failed, falling back to smart_route", exc_info=True)
        route_config = None
        cognitive_mode = "conversational"
        effective_model, was_downgraded = smart_route(lucy_state.preferred_model, user_content, history_len=len(history))

    from app.services.credits_service import CREDIT_RATES

    if effective_model not in CREDIT_RATES:
        logger.error("model_route returned unknown model %s, falling back to %s", effective_model, lucy_state.preferred_model)
        effective_model = lucy_state.preferred_model
        was_downgraded = False
        route_config = None
    if was_downgraded:
        logger.info(
            "Model route: %s -> %s (mode=%s) for user %s",
            lucy_state.preferred_model,
            effective_model,
            cognitive_mode,
            user_id,
        )

    # ── Gateway endpoint (shared only — no per-agent containers) ──
    if not (settings.openclaw_gateway_url and settings.openclaw_gateway_token):
        logger.error("Gateway not configured — check OPENCLAW_GATEWAY_URL and OPENCLAW_GATEWAY_TOKEN")
        yield json.dumps(
            {
                "type": "error",
                "code": "configuration_error",
                "message": "Gateway not configured",
            }
        )
        return

    gateway_url = f"{settings.openclaw_gateway_url}/v1/chat/completions"
    gateway_auth = f"Bearer {settings.openclaw_gateway_token}"

    payload = {
        "model": effective_model,
        "messages": history,
        "max_tokens": route_config.get("max_tokens", 4096) if route_config else 4096,
        "stream": True,
    }
    # Apply temperature from model router if available
    if route_config and "temperature" in route_config:
        payload["temperature"] = route_config["temperature"]

    full_content = ""
    tokens_input = 0
    tokens_output = 0

    headers = {
        "Authorization": gateway_auth,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", gateway_url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    logger.error("LiteLLM error %s: %s", response.status_code, body)
                    yield json.dumps(
                        {
                            "type": "error",
                            "code": "model_error",
                            "message": f"Model returned HTTP {response.status_code}",
                        }
                    )
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Extract content delta
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            full_content += content
                            yield json.dumps({"type": "stream", "content": content})

                    # Extract usage if present (final chunk)
                    usage = chunk.get("usage")
                    if usage:
                        tokens_input = usage.get("prompt_tokens", 0)
                        tokens_output = usage.get("completion_tokens", 0)

    except httpx.ConnectError as exc:
        logger.error("Cannot connect to shared gateway (%s): %s", gateway_url, exc)
        yield json.dumps(
            {
                "type": "error",
                "code": "connection_error",
                "message": "Cannot connect to model service",
            }
        )
        return
    except httpx.TimeoutException:
        yield json.dumps(
            {
                "type": "error",
                "code": "timeout",
                "message": "Model request timed out",
            }
        )
        return

    if not full_content:
        yield json.dumps(
            {
                "type": "error",
                "code": "empty_response",
                "message": "Model returned empty response",
            }
        )
        return

    # Estimate tokens if not provided by API
    if tokens_input == 0:
        tokens_input = max(1, len(str(history)) // 4)  # rough estimate
    if tokens_output == 0:
        tokens_output = max(1, len(full_content) // 4)

    # ── Safety Guard: record token usage ──
    guard.record_tokens(tokens_input + tokens_output)

    # ── Epistemic Humility: assess confidence & calibrate if needed ──
    try:
        epistemic_assessment = await assess_confidence(user_content, full_content)
        calibrated = await calibrate_response(
            full_content,
            epistemic_assessment,
            personality_type=lucy_state.personality_type,
        )
        if calibrated != full_content:
            # Stream the epistemic addendum to the client
            addendum = calibrated[len(full_content):]
            if addendum:
                yield json.dumps({"type": "stream", "content": addendum})
            full_content = calibrated
    except Exception:
        logger.debug("Epistemic calibration skipped", exc_info=True)

    # Deduct credits
    try:
        credits_used = await deduct_credits(
            db,
            user_id,
            effective_model,
            tokens_input,
            tokens_output,
        )
    except InsufficientCreditsError:
        # Still save the message but warn user
        credits_used = 0
        yield json.dumps(
            {
                "type": "error",
                "code": "insufficient_credits",
                "message": "Credits insufficient, please top up",
            }
        )

    # Save assistant message
    await save_message(
        db,
        conversation_id,
        MessageRole.assistant,
        full_content,
        model_name=effective_model,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        credits_used=credits_used,
    )

    # Update conversation title from first message
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if conv and conv.title == "New conversation":
        conv.title = user_content[:80]

    # ── Post-chat emotion & affection update ──
    updated_history = await get_conversation_history(db, conversation_id)

    new_mood = await analyze_mood(updated_history)
    lucy_state.mood = new_mood
    lucy_state.total_interactions = (lucy_state.total_interactions or 0) + 1
    lucy_state.last_interaction_at = datetime.now(UTC)

    affection_delta = calculate_affection_delta("chat", new_mood)
    lucy_state.affection = min(100, max(0, (lucy_state.affection or 0) + affection_delta))

    # Check for newly unlocked expressions
    all_unlocked = get_unlockable_expressions(lucy_state.affection)
    current_unlocked = lucy_state.unlocked_expressions or []
    if set(all_unlocked) != set(current_unlocked):
        lucy_state.unlocked_expressions = all_unlocked

    await db.commit()

    # Refresh user balance
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    balance = user.credit_balance if user else 0

    yield json.dumps(
        {
            "type": "done",
            "conversation_id": conversation_id,
            "usage": {
                "credits_used": credits_used,
                "balance": balance,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "model": effective_model,
                "routed": was_downgraded,
                "cognitive_mode": cognitive_mode,
            },
        }
    )

    # Background: extract memories from this conversation
    try:
        await extract_memories(db, user_id, LUCY_AGENT_ID, conversation_id, updated_history)
    except Exception:
        logger.debug("Memory extraction skipped", exc_info=True)

    # Background: record Lucy's existential experience (if significant)
    try:
        from app.services.existential_memory import process_conversation_for_experience

        user_mems = await get_relevant_memories(db, user_id, limit=5)
        await process_conversation_for_experience(db, user_id, updated_history, lucy_state, user_mems)
    except Exception:
        logger.debug("Experience recording skipped", exc_info=True)

    # Background: update symbiotic evolution cognitive profile
    try:
        from app.services.symbiotic_evolution import process_conversation_for_evolution

        await process_conversation_for_evolution(db, user_id, updated_history, lucy_state)
    except Exception:
        logger.debug("Symbiotic evolution update skipped", exc_info=True)


async def run_subtask(
    db: AsyncSession,
    user_id: str,
    lucy_state: LucyState,
    task_description: str,
    parent_conversation_id: str,
) -> str:
    """Run a sub-task: create a temporary conversation, get a single response."""
    conv = Conversation(agent_id=LUCY_AGENT_ID, title=f"[subtask] {task_description[:60]}")
    db.add(conv)
    await db.flush()
    await db.commit()

    full_response = ""
    async for event_str in stream_chat_completion(db, user_id, lucy_state, conv.id, task_description):
        event = json.loads(event_str)
        if event["type"] == "stream":
            full_response += event["content"]
        elif event["type"] == "error":
            full_response = f"[Subtask error: {event['message']}]"
            break

    return full_response
