"""Epistemic Humility Engine — Lucy knows what she doesn't know.

Unlike every other AI that presents everything with equal confidence,
Lucy has Bayesian meta-cognition: she estimates the reliability of her
own responses and communicates uncertainty honestly.

This is NOT about adding disclaimers. It's about Lucy genuinely understanding
when she's guessing vs. when she knows. The assessment is fast (cheap model,
short prompt) and only modifies behavior when confidence is actually low.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum

import litellm

logger = logging.getLogger(__name__)


class EpistemicStatus(str, Enum):
    CERTAIN = "certain"       # >95% confidence
    PROBABLE = "probable"     # 70-95%
    UNCERTAIN = "uncertain"   # 40-70%
    UNKNOWN = "unknown"       # <40%


@dataclass
class EpistemicAssessment:
    """Result of epistemic confidence assessment."""

    status: EpistemicStatus
    confidence: float  # 0.0 - 1.0
    uncertain_claims: list[str] = field(default_factory=list)
    verification_suggestions: list[str] = field(default_factory=list)


# ─── Assessment Prompt (kept SHORT for speed — under 200 tokens) ───

_ASSESS_PROMPT = """\
Rate the epistemic confidence of this AI response on a scale.
Consider: Is it factual or opinion? Could info be outdated? Is reasoning complex? Are there known failure modes?

Reply ONLY with JSON (no markdown):
{"status":"certain|probable|uncertain|unknown","confidence":0.0-1.0,"uncertain_claims":["..."],"verify":["..."]}

Keep arrays short (0-2 items). Empty arrays if confident."""


async def assess_confidence(
    query: str,
    response: str,
    context: dict | None = None,
) -> EpistemicAssessment:
    """Assess the epistemic status of a generated response.

    Uses a lightweight LLM call to evaluate:
    - Is this factual or opinion?
    - How recent/volatile is this information?
    - Is the reasoning chain long/complex?
    - Are there known failure modes?
    - Does this require domain expertise Lucy may lack?

    Returns: EpistemicAssessment with confidence level,
    specific uncertain claims, and verification suggestions.
    """
    # Short-circuit for very short responses (greetings, acknowledgments)
    if len(response) < 80:
        return EpistemicAssessment(
            status=EpistemicStatus.CERTAIN,
            confidence=0.98,
        )

    # Truncate to keep the assessment prompt fast
    truncated_response = response[:600] if len(response) > 600 else response
    truncated_query = query[:200] if len(query) > 200 else query

    user_content = f"Q: {truncated_query}\nA: {truncated_response}"

    try:
        result = await litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _ASSESS_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=150,
            temperature=0,
        )
        raw = result.choices[0].message.content.strip()

        # Parse JSON — handle potential markdown wrapping
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        data = json.loads(raw)

        status_str = data.get("status", "probable")
        try:
            status = EpistemicStatus(status_str)
        except ValueError:
            status = EpistemicStatus.PROBABLE

        confidence = float(data.get("confidence", 0.75))
        confidence = max(0.0, min(1.0, confidence))

        uncertain_claims = data.get("uncertain_claims", []) or []
        verify = data.get("verify", []) or []

        return EpistemicAssessment(
            status=status,
            confidence=confidence,
            uncertain_claims=uncertain_claims[:3],
            verification_suggestions=verify[:3],
        )

    except Exception:
        logger.debug("Epistemic assessment failed, defaulting to PROBABLE", exc_info=True)
        return EpistemicAssessment(
            status=EpistemicStatus.PROBABLE,
            confidence=0.75,
        )


# ─── Hedging Templates by Personality ───
# Lucy doesn't say "I'm an AI and I'm not sure" — she uses natural in-character hedging.

_HEDGING_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "少女": {
        "uncertain": [
            "这个我不太确定呢...我觉得可能是{claim}，但你最好验证一下~",
            "hmm、ここはちょっと自信ないかも。{claim}だと思うけど、確認した方がいいかも！",
            "I think it's {claim}, but don't quote me on that one~ ♪",
        ],
        "unknown": [
            "えっと...这个我真的不太知道诶 >_< {suggestion}",
            "ごめんね、ここは分からないの...{suggestion}",
            "Hmm, I genuinely don't know this one... {suggestion}",
        ],
    },
    "御姐": {
        "uncertain": [
            "这一点我不完全确定——{claim}，不过建议你确认一下。",
            "ここは少し不確かね。{claim}だと思うけど、検証した方がいいわ。",
            "I'd say {claim}, though I'd recommend verifying that.",
        ],
        "unknown": [
            "这个...坦白说我不确定。{suggestion}",
            "正直に言うと、ここは分からないわ。{suggestion}",
            "Honestly, I'm not sure about this one. {suggestion}",
        ],
    },
}


def _get_hedging_template(personality_type: str, level: str) -> str:
    """Pick a hedging template matching personality and uncertainty level."""
    templates = _HEDGING_TEMPLATES.get(personality_type, _HEDGING_TEMPLATES["少女"])
    options = templates.get(level, templates["uncertain"])
    return options[0]  # Deterministic for now; could rotate based on context


async def calibrate_response(
    original_response: str,
    assessment: EpistemicAssessment,
    personality_type: str = "少女",
) -> str:
    """If confidence is below threshold, modify the response to include
    appropriate epistemic markers.

    For UNCERTAIN/UNKNOWN: Add natural in-character hedging.
    The hedging style matches her personality (少女/御姐/custom).
    """
    # Only modify for low-confidence responses
    if assessment.status in (EpistemicStatus.CERTAIN, EpistemicStatus.PROBABLE):
        return original_response

    # Build a natural hedging note
    level = "unknown" if assessment.status == EpistemicStatus.UNKNOWN else "uncertain"

    claim_text = assessment.uncertain_claims[0] if assessment.uncertain_claims else "this"
    suggestion_text = (
        assessment.verification_suggestions[0]
        if assessment.verification_suggestions
        else "Maybe look it up to be sure?"
    )

    template = _get_hedging_template(personality_type, level)
    hedge = template.format(claim=claim_text, suggestion=suggestion_text)

    # Append the hedge naturally at the end rather than interrupting flow
    if original_response.endswith("\n"):
        return f"{original_response}\n{hedge}"
    return f"{original_response}\n\n{hedge}"


def should_verify(assessment: EpistemicAssessment) -> list[str]:
    """Return a list of specific claims that should be verified.

    e.g., ["The API endpoint might have changed after v3.2",
           "This regex pattern might not handle Unicode correctly"]
    """
    if assessment.status in (EpistemicStatus.CERTAIN, EpistemicStatus.PROBABLE):
        return []

    suggestions = list(assessment.verification_suggestions)
    # Add uncertain claims as implicit verification targets
    for claim in assessment.uncertain_claims:
        if claim not in suggestions:
            suggestions.append(claim)

    return suggestions[:5]
