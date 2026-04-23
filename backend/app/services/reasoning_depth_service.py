"""Adaptive reasoning depth selection.

Classifies query complexity and picks the optimal model to balance cost
and quality without changing the agent's stored model_name.

Depth levels:
  shallow  → fast/cheap model (qwen-turbo)  — simple lookups, translations
  standard → agent's configured model        — everyday tasks
  deep     → reasoning model (deepseek-reasoner) — math, code, analysis
"""

import re

_DEEP_RE = re.compile(
    r"\b(证明|推导|优化|设计|架构|分析|对比|评估|为什么|如何解决|调试|"
    r"debug|solve|prove|optim|design|architect|analyz|compar|evaluat|"
    r"explain why|step.by.step|algorithm|reasoning|inference|"
    r"calculate|derive|implement|refactor|性能|复杂度|complexity)\b",
    re.IGNORECASE,
)

_SHALLOW_RE = re.compile(
    r"\b(translate|翻译|what is|what are|who is|when did|where is|"
    r"list|格式化|format|summarize|总结|convert|转换|define|定义|"
    r"spell|rewrite|改写)\b",
    re.IGNORECASE,
)

_SHALLOW_MODEL = "qwen-turbo"
_DEEP_MODEL = "deepseek-reasoner"

# Content length above which shallow signals are ignored (likely more complex)
_SHALLOW_MAX_LEN = 200


def classify_depth(user_content: str) -> str:
    """Return 'shallow', 'standard', or 'deep' for the given query."""
    if _DEEP_RE.search(user_content):
        return "deep"
    if _SHALLOW_RE.search(user_content) and len(user_content) < _SHALLOW_MAX_LEN:
        return "shallow"
    return "standard"


def select_adaptive_model(agent_model: str, user_content: str) -> tuple[str, str]:
    """Return (model_to_use, depth_level).

    Only called when the agent has adaptive_depth enabled.
    Keeps the agent's model for standard-depth tasks so the user's
    explicit choice is still honoured when the query is neither very
    simple nor very complex.
    """
    depth = classify_depth(user_content)
    if depth == "shallow":
        return _SHALLOW_MODEL, depth
    if depth == "deep":
        return _DEEP_MODEL, depth
    return agent_model, depth
