"""模型备用链 — 主模型挂了自动切到下一个。

策略：同级别替换优先，最后兜底最便宜的模型。
链条是静态的、可预测的，不做动态发现（避免误路由到贵价模型）。
"""

MODEL_FALLBACK_CHAIN: dict[str, list[str]] = {
    # 标准级
    "deepseek-chat":     ["qwen-plus", "qwen-turbo", "gpt-4o-mini"],
    "qwen-turbo":        ["deepseek-chat", "qwen-plus", "gpt-4o-mini"],
    "qwen-plus":         ["deepseek-chat", "qwen-turbo", "gpt-4o-mini"],
    "qwen-max":          ["deepseek-chat", "qwen-plus", "gpt-4o-mini"],
    "claude-haiku":      ["gpt-4o-mini", "deepseek-chat", "qwen-plus"],
    "gpt-4o-mini":       ["claude-haiku", "deepseek-chat", "qwen-turbo"],
    "gemini-flash":      ["qwen-turbo", "deepseek-chat", "gpt-4o-mini"],

    # 高级
    "deepseek-reasoner": ["qwen-max", "gpt-4o", "claude-sonnet"],
    "claude-sonnet":     ["gpt-4o", "deepseek-reasoner", "qwen-max"],
    "gpt-4o":            ["claude-sonnet", "deepseek-reasoner", "qwen-max"],
}


def get_fallback_models(primary_model: str) -> list[str]:
    """返回按优先级排序的备用模型列表。"""
    return MODEL_FALLBACK_CHAIN.get(primary_model, ["deepseek-chat", "qwen-turbo"])
