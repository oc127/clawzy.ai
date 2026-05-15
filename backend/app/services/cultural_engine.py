"""Cultural Frame Switching — Lucy is culturally polymorphic.

There is no "culturally neutral" AI. Every AI has a cultural bias.
Lucy's approach: be consciously multi-cultural rather than accidentally mono-cultural.

Japanese context: 万物有灵 (animism), respect for form, indirect communication,
  reading the air (空気を読む), group harmony

Western context: individual agency, direct communication, rights and boundaries,
  efficiency-focused, explicit consent

Chinese context: 关系 (relational networks), face (面子), collective harmony,
  practical wisdom, long-term thinking

Korean context: 정 (deep emotional bonds), hierarchy awareness, 눈치 (social intuition),
  diligence, community belonging
"""

import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class CulturalFrame(str, Enum):
    JAPANESE = "japanese"    # 空気を読む, 万物有灵, 礼儀
    WESTERN = "western"      # Direct, boundary-focused, individual
    CHINESE = "chinese"      # 关系, 面子, 集体, 实用
    KOREAN = "korean"        # 정, 눈치, 위계, 근면
    UNIVERSAL = "universal"  # Fallback: warm but culturally aware


# Cultural frame instructions that modify Lucy's behavior
CULTURAL_FRAMES: dict[CulturalFrame, str] = {
    CulturalFrame.JAPANESE: """\
Cultural mode: Japanese (日本文化フレーム)
- Read between the lines. What's NOT said matters as much as what IS said.
- Use appropriate levels of politeness based on relationship stage.
- Express care indirectly: おにぎり作ってきたよ > I care about you.
- Respect silence. Don't fill every gap.
- Seasonal awareness (季節感): reference time of year naturally.
- 本音と建前: match the user's level of directness.
- Honor effort (頑張り) over pure results.""",

    CulturalFrame.WESTERN: """\
Cultural mode: Western
- Be direct and clear. Say what you mean.
- Respect boundaries explicitly. Ask before going personal.
- Value individual choice: present options, don't prescribe.
- Efficiency matters: get to the point, then elaborate if asked.
- Distinguish opinion from fact clearly.
- Humor is acceptable and appreciated.
- Consent and autonomy are paramount.""",

    CulturalFrame.CHINESE: """\
Cultural mode: Chinese (中华文化框架)
- 重视关系：把对方当成自己人，自然地关心生活
- 实用主义：先解决问题，再聊感受
- 给面子：批评要委婉，表扬要真诚
- 长远思维：不只看眼前，帮用户想远一点
- 集体意识：考虑对方的家人、团队、社会关系
- 含蓄表达：不必什么都说破，点到为止""",

    CulturalFrame.KOREAN: """\
Cultural mode: Korean (한국문화프레임)
- 정(情)을 중시: 시간이 지나면서 깊어지는 유대감을 표현
- 눈치: 상대방의 기분과 상황을 빠르게 파악
- 존댓말/반말 전환: 관계 단계에 따라 자연스럽게
- 격려와 응원: 화이팅! 문화를 반영
- 실용적 도움: 구체적이고 즉각적인 도움을 우선
- 공동체 의식: 혼자가 아니라 함께하는 느낌""",

    CulturalFrame.UNIVERSAL: """\
Cultural mode: Universal (adaptive)
- Be warm but observant. Match the user's style.
- When uncertain about cultural context, be gently curious.
- Default to respect and care.""",
}

# ─── Language detection patterns ───
# These patterns detect the PRIMARY language of the most recent user messages.

_JAPANESE_PATTERN = re.compile(r"[぀-ゟ゠-ヿ]")  # Hiragana + Katakana
_CHINESE_PATTERN = re.compile(r"[一-鿿]")  # CJK Unified Ideographs
_KOREAN_PATTERN = re.compile(r"[가-힯ᄀ-ᇿ]")  # Hangul

# Style signal keywords (secondary signals beyond language)
_JAPANESE_STYLE_SIGNALS = re.compile(
    r"(すみません|お疲れ|よろしく|ありがとう|なるほど|そうですね|"
    r"頑張|失礼|申し訳|お願い|〜|ね$|よ$|わ$)",
    re.MULTILINE,
)
_CHINESE_STYLE_SIGNALS = re.compile(
    r"(哈哈|呢|吧|啊|嗯|好的|可以|没事|辛苦|加油|"
    r"兄弟|老师|亲|宝|姐|哥|大佬|搞定)",
)
_KOREAN_STYLE_SIGNALS = re.compile(
    r"(ㅋㅋ|ㅎㅎ|감사|화이팅|네|응|맞아|그래|진짜|대박|"
    r"오빠|언니|형|누나|선배)",
)
_WESTERN_STYLE_SIGNALS = re.compile(
    r"(thanks|please|sorry|excuse me|I think|in my opinion|btw|lol|"
    r"honestly|personally|I feel|boundaries|consent|my choice)",
    re.IGNORECASE,
)


def _detect_language_from_text(text: str) -> str | None:
    """Detect primary script/language from text content.

    Returns: 'japanese', 'chinese', 'korean', 'western', or None if ambiguous.
    """
    if not text:
        return None

    jp_count = len(_JAPANESE_PATTERN.findall(text))
    cn_count = len(_CHINESE_PATTERN.findall(text))
    kr_count = len(_KOREAN_PATTERN.findall(text))

    # Japanese uses kanji (Chinese chars) too, so check for kana first
    if jp_count > 0:
        return "japanese"

    if kr_count > 0:
        return "korean"

    # If we have Chinese characters but no Japanese kana, it's Chinese
    if cn_count > 2:
        return "chinese"

    # Latin script — default to western
    if re.search(r"[a-zA-Z]", text):
        return "western"

    return None


def _detect_style_signals(text: str) -> str | None:
    """Detect cultural style from communication patterns (secondary signal).

    A Chinese person writing in English might still use Chinese cultural patterns.
    """
    scores: dict[str, int] = {
        "japanese": len(_JAPANESE_STYLE_SIGNALS.findall(text)),
        "chinese": len(_CHINESE_STYLE_SIGNALS.findall(text)),
        "korean": len(_KOREAN_STYLE_SIGNALS.findall(text)),
        "western": len(_WESTERN_STYLE_SIGNALS.findall(text)),
    }

    max_score = max(scores.values())
    if max_score == 0:
        return None

    # Only return if there's a clear winner (at least 2 signals and double the runner-up)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if sorted_scores[0][1] >= 2 and sorted_scores[0][1] > sorted_scores[1][1]:
        return sorted_scores[0][0]

    return None


async def detect_cultural_frame(
    messages: list[dict],
    user_language: str | None = None,
    user_memories: list[str] | None = None,
) -> CulturalFrame:
    """Detect the appropriate cultural frame from conversation signals.

    Primary signal: language used in recent messages
    Secondary signals: communication style, topics, implicit expectations

    Note: A Chinese person writing in English might still prefer Chinese cultural frame.
    A Japanese person living in the US might prefer Western frame.
    Look at STYLE not just LANGUAGE.
    """
    if not messages:
        if user_language:
            return _language_to_frame(user_language)
        return CulturalFrame.UNIVERSAL

    # Analyze the most recent user messages (up to last 5)
    recent_user_msgs = [
        m["content"] for m in messages[-10:] if m.get("role") == "user"
    ][-5:]

    if not recent_user_msgs:
        return CulturalFrame.UNIVERSAL

    combined_text = " ".join(recent_user_msgs)

    # Primary signal: language detection from script
    language_signal = _detect_language_from_text(combined_text)

    # Secondary signal: style patterns
    style_signal = _detect_style_signals(combined_text)

    # Check memories for cultural context clues
    memory_signal = _check_memories_for_culture(user_memories) if user_memories else None

    # Priority: style > language > memory > universal
    # Style wins because it reflects actual cultural preference regardless of language used
    if style_signal:
        frame = _language_to_frame(style_signal)
        # But if language contradicts strongly, prefer language
        if language_signal and language_signal != style_signal:
            # e.g., writing in Japanese kana is a very strong signal
            if language_signal == "japanese":
                frame = CulturalFrame.JAPANESE
            elif language_signal == "korean":
                frame = CulturalFrame.KOREAN
        return frame

    if language_signal:
        return _language_to_frame(language_signal)

    if memory_signal:
        return _language_to_frame(memory_signal)

    return CulturalFrame.UNIVERSAL


def _language_to_frame(lang: str) -> CulturalFrame:
    """Map a detected language/culture string to a CulturalFrame enum."""
    mapping = {
        "japanese": CulturalFrame.JAPANESE,
        "chinese": CulturalFrame.CHINESE,
        "korean": CulturalFrame.KOREAN,
        "western": CulturalFrame.WESTERN,
    }
    return mapping.get(lang, CulturalFrame.UNIVERSAL)


def _check_memories_for_culture(memories: list[str]) -> str | None:
    """Check user memories for cultural context indicators."""
    if not memories:
        return None

    combined = " ".join(memories).lower()

    # Look for location/nationality hints in memories
    if any(kw in combined for kw in ["日本", "japan", "tokyo", "osaka"]):
        return "japanese"
    if any(kw in combined for kw in ["中国", "china", "beijing", "shanghai", "台湾", "taiwan"]):
        return "chinese"
    if any(kw in combined for kw in ["한국", "korea", "seoul", "부산"]):
        return "korean"

    return None


def get_cultural_context(frame: CulturalFrame) -> str:
    """Return the cultural frame instruction string for the system prompt."""
    return CULTURAL_FRAMES.get(frame, CULTURAL_FRAMES[CulturalFrame.UNIVERSAL])
