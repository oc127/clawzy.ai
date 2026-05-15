"""Smart model routing — auto-downgrades simple tasks to cheaper models.

Inspired by 秋芝 Qclaw's "预算管家" smart routing:
- Short, simple messages → use the cheapest available model
- Complex messages (long, code, reasoning keywords) → keep the premium model
"""

import re

# Models grouped by tier cost (cheapest first)
DOWNGRADE_MAP: dict[str, str] = {
    # Premium → Standard fallback pairs (same provider preferred)
    "claude-sonnet": "claude-haiku",
    "gpt-4o": "gpt-4o-mini",
    "deepseek-reasoner": "deepseek-chat",
    "qwen-max": "qwen-turbo",
    "qwen-plus": "qwen-turbo",
}

# Keywords that suggest a complex task (should use the premium model)
COMPLEX_INDICATORS = re.compile(
    r"(分析|analyze|explain|compare|reason|debug|review|refactor|architect|"
    r"optimize|implement|design|评测|深度|详细|comprehensive|step[- ]by[- ]step|"
    r"write.*code|写.*代码|算法|algorithm|数学|math|proof|证明|"
    r"翻译.*全文|translate.*entire|summarize.*article|总结.*文章)",
    re.IGNORECASE,
)

# Code block indicators
CODE_PATTERN = re.compile(r"```|def |class |function |import |from |const |let |var ")


def classify_complexity(message: str, history_len: int) -> str:
    """Classify a message as 'simple' or 'complex'.

    Returns 'simple' if the task is straightforward and can use a cheaper model.
    Returns 'complex' if the task needs the full power of the selected model.
    """
    # Long messages are likely complex
    if len(message) > 500:
        return "complex"

    # Messages with code are complex
    if CODE_PATTERN.search(message):
        return "complex"

    # Messages with complexity keywords are complex
    if COMPLEX_INDICATORS.search(message):
        return "complex"

    # Deep conversation (many turns) stays on premium
    if history_len > 10:
        return "complex"

    # Short, casual messages are simple
    return "simple"


def smart_route(model_name: str, message: str, history_len: int = 0) -> tuple[str, bool]:
    """Determine the best model for a given message.

    Returns (model_to_use, was_downgraded).
    """
    # Only downgrade if the model has a cheaper alternative
    downgrade_target = DOWNGRADE_MAP.get(model_name)
    if not downgrade_target:
        return model_name, False

    complexity = classify_complexity(message, history_len)
    if complexity == "simple":
        return downgrade_target, True

    return model_name, False
