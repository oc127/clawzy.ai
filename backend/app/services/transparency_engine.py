"""Adaptive Transparency — Lucy adjusts explanation depth to the user.

A beginner gets intuitive analogies.
An expert gets the reasoning chain.
A child gets stories.
The same Lucy, different communication strategies.
"""

import json
import logging
from enum import Enum

import litellm

logger = logging.getLogger(__name__)


class UserLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    CHILD = "child"


# ─── Assessment Prompt (lightweight, fast) ───

_LEVEL_ASSESS_PROMPT = """\
Classify this user's technical level from their messages.
Signals: vocabulary, question specificity, jargon usage, problem framing.

Reply with EXACTLY one word: beginner, intermediate, expert, or child"""


async def assess_user_level(
    messages: list[dict],
    user_memories: list[str] | None = None,
) -> UserLevel:
    """Infer user's technical level from conversation history and memories.

    Signals: vocabulary complexity, question specificity,
    technical terms used correctly, problem framing style.
    """
    valid_levels = {level.value for level in UserLevel}

    if not messages:
        return UserLevel.INTERMEDIATE

    # Use recent user messages only for assessment
    user_msgs = [m["content"] for m in messages[-8:] if m.get("role") == "user"]
    if not user_msgs:
        return UserLevel.INTERMEDIATE

    # Build assessment input
    sample = "\n".join(user_msgs[-5:])[:500]

    # Include memory hints if available
    memory_hint = ""
    if user_memories:
        relevant = [m for m in user_memories if any(
            kw in m.lower() for kw in ("developer", "engineer", "student", "beginner", "child", "kid", "expert", "senior", "junior")
        )]
        if relevant:
            memory_hint = f"\nKnown about user: {'; '.join(relevant[:3])}"

    try:
        result = await litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _LEVEL_ASSESS_PROMPT},
                {"role": "user", "content": sample + memory_hint},
            ],
            max_tokens=10,
            temperature=0,
        )
        level_str = result.choices[0].message.content.strip().lower()

        # Extract valid level from response
        if level_str in valid_levels:
            return UserLevel(level_str)
        for level in valid_levels:
            if level in level_str:
                return UserLevel(level)

        return UserLevel.INTERMEDIATE

    except Exception:
        logger.debug("User level assessment failed, defaulting to INTERMEDIATE", exc_info=True)
        return UserLevel.INTERMEDIATE


# ─── Transparency Instructions (injected into system prompt) ───

_TRANSPARENCY_INSTRUCTIONS: dict[UserLevel, str] = {
    UserLevel.EXPERT: (
        "The user is technically advanced. Show your reasoning. Include edge cases "
        "and caveats. Use precise terminology without over-explaining. "
        "They can handle raw complexity — don't simplify unnecessarily."
    ),
    UserLevel.INTERMEDIATE: (
        "The user has moderate technical knowledge. Explain key decisions briefly. "
        "Define non-obvious terms if used. Balance depth with clarity."
    ),
    UserLevel.BEGINNER: (
        "The user is learning. Use analogies and metaphors. Explain step by step. "
        "Avoid jargon or define it immediately. Offer to go deeper if they want. "
        "Be encouraging — learning is hard and they're doing great."
    ),
    UserLevel.CHILD: (
        "The user is young or very new to this. Use stories and comparisons to "
        "everyday things. Keep explanations playful and encouraging. "
        "Celebrate their understanding. Use short sentences."
    ),
}

# Task-specific adjustments
_TASK_ADJUSTMENTS: dict[str, dict[UserLevel, str]] = {
    "code": {
        UserLevel.EXPERT: "Skip boilerplate explanations. Focus on the interesting design decisions.",
        UserLevel.BEGINNER: "Comment the code heavily. Explain what each part does and why.",
        UserLevel.CHILD: "Show the code like building blocks. Explain what each piece does in simple terms.",
    },
    "explanation": {
        UserLevel.EXPERT: "Be concise. They likely know the basics — focus on nuance.",
        UserLevel.BEGINNER: "Start with the big picture, then zoom in step by step.",
        UserLevel.CHILD: "Start with a story or analogy. Make it fun and relatable.",
    },
    "debugging": {
        UserLevel.EXPERT: "Jump to root cause analysis. Show the reasoning chain.",
        UserLevel.BEGINNER: "Walk through the debugging process so they can learn the method.",
    },
}


def get_transparency_instructions(level: UserLevel, task_type: str | None = None) -> str:
    """Return system prompt additions that guide Lucy's explanation depth.

    Args:
        level: The assessed user level.
        task_type: Optional task category (code, explanation, debugging) for
                   task-specific guidance.

    Returns:
        A string to append to the system prompt.
    """
    base = _TRANSPARENCY_INSTRUCTIONS[level]

    # Add task-specific guidance if available
    if task_type and task_type in _TASK_ADJUSTMENTS:
        task_adj = _TASK_ADJUSTMENTS[task_type].get(level)
        if task_adj:
            return f"{base}\n{task_adj}"

    return base


def detect_task_type(query: str) -> str | None:
    """Simple heuristic to detect what kind of task the user is asking about."""
    query_lower = query.lower()

    code_signals = ("code", "function", "implement", "写代码", "コード", "bug", "error",
                    "fix", "class", "api", "endpoint", "script", "program")
    debug_signals = ("debug", "error", "traceback", "doesn't work", "failed",
                     "not working", "动かない", "报错", "バグ")
    explain_signals = ("explain", "what is", "how does", "why", "什么是", "为什么",
                       "どうして", "なぜ", "教えて")

    if any(s in query_lower for s in debug_signals):
        return "debugging"
    if any(s in query_lower for s in code_signals):
        return "code"
    if any(s in query_lower for s in explain_signals):
        return "explanation"

    return None


async def adapt_response(
    response: str,
    user_level: UserLevel,
    original_query: str,
) -> str:
    """Post-process a response to match the user's level.

    Only called if the response seems mismatched to the user's level.
    Most of the time, the system prompt instructions are enough.
    This is a safety net for cases where the response is clearly too
    complex for the user or too simple for an expert.
    """
    # Heuristic: only adapt if there's a clear mismatch
    response_complexity = _estimate_complexity(response)

    if user_level == UserLevel.BEGINNER and response_complexity == "high":
        # Response is too complex for a beginner — simplify
        pass  # Fall through to LLM adaptation
    elif user_level == UserLevel.EXPERT and response_complexity == "low" and len(response) > 200:
        # Response is overly simplified for an expert — this is fine, skip
        return response
    else:
        # No mismatch detected — return as-is
        return response

    # Use LLM to adapt (rare path — only for clear mismatches)
    try:
        adapt_prompt = (
            f"Rewrite this response for a {user_level.value}-level user. "
            f"Keep the same information but adjust complexity and explanation depth. "
            f"Maintain Lucy's personality — warm, caring, in-character. "
            f"Keep the same language as the original."
        )

        result = await litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": adapt_prompt},
                {"role": "user", "content": f"Original query: {original_query[:200]}\n\nResponse to adapt:\n{response}"},
            ],
            max_tokens=2000,
            temperature=0.3,
        )
        adapted = result.choices[0].message.content.strip()
        if adapted and len(adapted) > 20:
            return adapted
    except Exception:
        logger.debug("Response adaptation failed, returning original", exc_info=True)

    return response


def _estimate_complexity(text: str) -> str:
    """Quick heuristic to estimate response complexity level."""
    indicators = 0

    # Code blocks
    if "```" in text:
        indicators += 2

    # Technical jargon density (rough proxy)
    technical_terms = (
        "algorithm", "complexity", "implementation", "architecture", "paradigm",
        "polymorphism", "abstraction", "concurrency", "asynchronous", "middleware",
        "serialization", "deserialization", "idempotent", "deterministic",
    )
    term_count = sum(1 for t in technical_terms if t in text.lower())
    if term_count >= 3:
        indicators += 2
    elif term_count >= 1:
        indicators += 1

    # Long paragraphs
    if len(text) > 1000:
        indicators += 1

    # Nested lists or complex structure
    if text.count("\n- ") > 5 or text.count("\n  - ") > 2:
        indicators += 1

    if indicators >= 3:
        return "high"
    elif indicators >= 1:
        return "medium"
    return "low"
