"""Morphogenic Fluidity — Lucy chooses her own cognitive mode.

Instead of one model for everything, Lucy selects the optimal reasoning
paradigm for each task:
- Code/logic tasks -> code-specialized model (deepseek-coder)
- Creative writing -> high-temperature creative model
- Simple chat -> fast lightweight model (saves cost + latency)
- Complex reasoning -> reasoning model (deepseek-reasoner)
- Translation/factual -> multilingual-specialized model

This isn't just model selection — it's Lucy choosing HOW to think.
"""

import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class CognitiveMode(str, Enum):
    ANALYTICAL = "analytical"    # Code, math, logic, debugging
    CREATIVE = "creative"        # Writing, brainstorming, art
    CONVERSATIONAL = "conversational"  # Casual chat, emotional support
    REASONING = "reasoning"      # Complex multi-step problems
    FACTUAL = "factual"          # Knowledge retrieval, translation


# Model mapping per cognitive mode
MODE_MODELS: dict[CognitiveMode, dict] = {
    CognitiveMode.ANALYTICAL: {
        "model": "deepseek-chat",
        "temperature": 0.1,
        "max_tokens": 4096,
    },
    CognitiveMode.CREATIVE: {
        "model": "deepseek-chat",
        "temperature": 0.9,
        "max_tokens": 2048,
    },
    CognitiveMode.CONVERSATIONAL: {
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 1024,
    },
    CognitiveMode.REASONING: {
        "model": "deepseek-reasoner",
        "temperature": 0.2,
        "max_tokens": 4096,
    },
    CognitiveMode.FACTUAL: {
        "model": "deepseek-chat",
        "temperature": 0.1,
        "max_tokens": 2048,
    },
}

# ─── Heuristic classification patterns ───

_CODE_PATTERNS = re.compile(
    r"(```|def |class |function |import |from |const |let |var |"
    r"print\(|console\.|System\.|#include|public static|"
    r"SELECT |INSERT |CREATE TABLE|ALTER TABLE|"
    r"<div|<span|<html|\.css|\.js|\.py|\.ts|"
    r"写代码|写个|コードを|code|debug|bug|error|traceback|exception|"
    r"\bapi\b|endpoint|database|query|schema|migration|deploy|"
    r"git |docker |npm |pip |cargo )",
    re.IGNORECASE,
)

_ANALYTICAL_PATTERNS = re.compile(
    r"(analyze|分析|解析|optimize|优化|最適化|refactor|重构|"
    r"debug|调试|デバッグ|performance|性能|benchmark|"
    r"algorithm|算法|アルゴリズム|data structure|"
    r"time complexity|space complexity|计算|数学|math|"
    r"prove|证明|equation|formula|calculate|算出)",
    re.IGNORECASE,
)

_CREATIVE_PATTERNS = re.compile(
    r"(write.*story|write.*poem|write.*essay|write.*song|"
    r"creative|brainstorm|imagine|创作|写.*故事|写.*诗|"
    r"作文|小说|脚本|scenario|fiction|"
    r"物語|詩|創作|ストーリー|"
    r"design.*name|think.*idea|come up with|"
    r"글.*써|이야기|소설|시.*써)",
    re.IGNORECASE,
)

_REASONING_PATTERNS = re.compile(
    r"(why.*\?|how does.*work|explain.*detail|"
    r"compare.*and.*|pros.*cons|trade.?off|"
    r"step.by.step|think through|reason|论证|"
    r"因为.*所以|为什么|怎么.*的|原理|"
    r"なぜ|どうして|仕組み|理由|"
    r"왜|어떻게.*되|원리|이유)",
    re.IGNORECASE,
)

_FACTUAL_PATTERNS = re.compile(
    r"(what is|what are|who is|when did|where is|"
    r"translate|翻译|翻訳|번역|"
    r"define|definition|meaning of|"
    r"是什么|是谁|什么时候|在哪|"
    r"とは|何ですか|いつ|どこ|"
    r"뭐야|누구|언제|어디)",
    re.IGNORECASE,
)

_CONVERSATIONAL_PATTERNS = re.compile(
    r"(^(hi|hey|hello|sup|yo|嗨|你好|おはよ|こんにち|안녕|ㅎㅇ)[\s!?]*$|"
    r"^.{1,20}$|"  # Very short messages are usually conversational
    r"how are you|how's it going|what's up|"
    r"感觉|心情|好累|开心|难过|想你|"
    r"気分|疲れ|嬉しい|寂しい|会いたい|"
    r"기분|피곤|행복|보고싶|"
    r"thanks|thank you|谢谢|ありがとう|고마워|"
    r"good morning|good night|おやすみ|早安|晚安|잘자)",
    re.IGNORECASE,
)


async def classify_task(
    message: str,
    conversation_context: list[dict] | None = None,
) -> CognitiveMode:
    """Classify the user's message into a cognitive mode.

    Uses fast heuristics first (keyword matching, regex patterns),
    falls back to CONVERSATIONAL when ambiguous (cheapest default).

    Heuristics:
    - Contains code blocks or asks about code -> ANALYTICAL
    - Asks to write/create/imagine -> CREATIVE
    - Short casual messages, greetings, emotions -> CONVERSATIONAL
    - "Why", "How does X work", multi-part questions -> REASONING
    - "What is", translation, fact lookup -> FACTUAL
    """
    # Check conversational first — short messages are the most common case
    if len(message.strip()) <= 20 or _CONVERSATIONAL_PATTERNS.search(message):
        # But don't classify code snippets as conversational
        if not _CODE_PATTERNS.search(message):
            return CognitiveMode.CONVERSATIONAL

    # Code and analytical patterns are strong signals
    if _CODE_PATTERNS.search(message):
        # Distinguish between code-with-reasoning and pure code
        if _REASONING_PATTERNS.search(message):
            return CognitiveMode.REASONING
        return CognitiveMode.ANALYTICAL

    if _ANALYTICAL_PATTERNS.search(message):
        return CognitiveMode.ANALYTICAL

    # Creative tasks
    if _CREATIVE_PATTERNS.search(message):
        return CognitiveMode.CREATIVE

    # Reasoning tasks — multi-step, "why", comparisons
    if _REASONING_PATTERNS.search(message):
        return CognitiveMode.REASONING

    # Factual lookups and translations
    if _FACTUAL_PATTERNS.search(message):
        return CognitiveMode.FACTUAL

    # Long messages without clear signals — likely need reasoning
    if len(message) > 300:
        return CognitiveMode.REASONING

    # Default: conversational (cheapest, fastest)
    return CognitiveMode.CONVERSATIONAL


def get_model_config(mode: CognitiveMode, user_preferred_model: str | None = None) -> dict:
    """Get the model configuration for a cognitive mode.

    If user has set a preferred model, respect that for CONVERSATIONAL mode.
    For specialized modes (ANALYTICAL, REASONING), use specialized models
    unless the user's preferred model is already premium enough.
    """
    base_config = MODE_MODELS[mode].copy()

    if not user_preferred_model:
        return base_config

    # For conversational mode, always respect user preference
    if mode == CognitiveMode.CONVERSATIONAL:
        base_config["model"] = user_preferred_model
        return base_config

    # For reasoning mode, use deepseek-reasoner unless user chose a premium reasoning model
    premium_reasoning = {"claude-sonnet", "gpt-4o", "deepseek-reasoner"}
    if mode == CognitiveMode.REASONING:
        if user_preferred_model in premium_reasoning:
            base_config["model"] = user_preferred_model
        return base_config

    # For analytical/creative/factual, use user's preferred model if it's capable
    capable_models = {"deepseek-chat", "claude-sonnet", "gpt-4o", "qwen-max", "qwen-plus"}
    if user_preferred_model in capable_models:
        base_config["model"] = user_preferred_model

    return base_config


async def route(
    message: str,
    conversation_context: list[dict] | None = None,
    user_preferred_model: str | None = None,
) -> dict:
    """Main entry point: classify task and return full model config.

    Returns: {"model": "...", "temperature": ..., "max_tokens": ..., "cognitive_mode": "..."}
    """
    mode = await classify_task(message, conversation_context)
    config = get_model_config(mode, user_preferred_model)
    config["cognitive_mode"] = mode.value

    logger.debug(
        "Model router: message=%r -> mode=%s, model=%s",
        message[:50],
        mode.value,
        config["model"],
    )

    return config
