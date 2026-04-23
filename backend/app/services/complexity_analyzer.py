import asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)

_LEVEL_MODELS: dict[str, str] = {
    "simple":   "deepseek-chat",
    "moderate": "qwen-plus",
    "complex":  "deepseek-reasoner",
    "expert":   "qwen-max",
}

_LEVEL_DEPTH: dict[str, int] = {
    "simple":   1,
    "moderate": 2,
    "complex":  3,
    "expert":   4,
}

_SIMPLE_RE = re.compile(
    r"^(こんにちは|おはよう|こんばんは|ありがとう|はい|いいえ|"
    r"hello|hi|hey|thanks|thank you|yes|no|okay|ok|sure|"
    r"你好|谢谢|是|否|안녕|감사|네|아니|"
    r"今(何時|日の天気|日は)|what time|what('s| is) the (time|weather)|"
    r"who are you|あなたは誰|how are you|お元気ですか)",
    re.IGNORECASE,
)

_EXPERT_RE = re.compile(
    r"(comprehensive|詳細な|詳しく|完全な|exhaustive|"
    r"research paper|研究論文|thesis|レポート作成|"
    r"multiple.*aspect|様々な観点|cross.?domain|複数の分野|"
    r"in.?depth analysis|深い分析|white.?paper)",
    re.IGNORECASE,
)

_COMPLEX_RE = re.compile(
    r"(分析|比較|検討|設計|アーキテクチャ|システム設計|実装|リファクタ|"
    r"analyze|compare|design|architect|implement|refactor|"
    r"step by step|ステップ|手順|algorithm|アルゴリズム|"
    r"pros and cons|メリット|デメリット|trade.?off|"
    r"research|調査|report|レポート|論文|essay)",
    re.IGNORECASE,
)

_CODE_RE = re.compile(
    r"(コード|code|function|関数|class|クラス|bug|バグ|"
    r"error|エラー|script|スクリプト|program|プログラム|"
    r"api|endpoint|database|sql|query|fix|debug)",
    re.IGNORECASE,
)

_TOOLS_RE = re.compile(
    r"(search|検索|find|look up|調べ|web|internet|browse|ブラウズ)",
    re.IGNORECASE,
)

_LLM_PROMPT = """Classify this message into exactly one level: simple, moderate, complex, or expert.

- simple: greetings, single short questions, yes/no, weather/time
- moderate: technical questions, code help, factual queries with some depth
- complex: multi-step analysis, code generation, comparisons, design questions
- expert: comprehensive research, cross-domain analysis, long-form writing, system architecture

Message: {message}

Respond ONLY with valid JSON: {{"level": "<level>"}}"""


def _rule_engine(message: str) -> tuple[str, float]:
    """Return (level, confidence). Confidence <0.75 triggers LLM fallback."""
    s = message.strip()
    n = len(s)

    if n <= 20 or _SIMPLE_RE.search(s):
        return "simple", 0.95

    if _EXPERT_RE.search(s) and n > 100:
        return "expert", 0.85

    if _COMPLEX_RE.search(s):
        return ("expert" if n > 300 else "complex"), 0.85

    if _CODE_RE.search(s):
        return ("complex" if n > 200 else "moderate"), 0.85

    if n <= 50:
        return "simple", 0.80
    if n <= 200:
        return "moderate", 0.70
    if n <= 500:
        return "complex", 0.65

    return "expert", 0.60


async def _llm_classify(message: str) -> str:
    """Cheapest LLM call for uncertain cases. Times out in 3s, falls back to 'moderate'."""
    try:
        from app.core.http_client import get_litellm_client

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": _LLM_PROMPT.format(message=message[:500]),
                }
            ],
            "max_tokens": 20,
            "temperature": 0.0,
        }
        client = get_litellm_client()
        resp = await asyncio.wait_for(
            client.post("/v1/chat/completions", json=payload),
            timeout=3.0,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        data = json.loads(raw)
        level = data.get("level", "moderate")
        if level in _LEVEL_MODELS:
            return level
    except Exception as exc:
        logger.warning("LLM complexity classification failed: %s", exc)
    return "moderate"


async def analyze_complexity(message: str) -> dict:
    """
    Analyze message complexity to determine reasoning depth and model routing.

    Returns dict with keys: level, reasoning_depth, recommended_model,
    estimated_tokens, needs_tools, needs_multi_step, explanation.
    """
    level, confidence = _rule_engine(message)

    if confidence < 0.75:
        level = await _llm_classify(message)

    words = len(message.split())
    return {
        "level": level,
        "reasoning_depth": _LEVEL_DEPTH[level],
        "recommended_model": _LEVEL_MODELS[level],
        "estimated_tokens": min(500 + words * 20, 4000),
        "needs_tools": bool(_TOOLS_RE.search(message)),
        "needs_multi_step": level in ("complex", "expert"),
        "explanation": f"{level} (rule confidence={confidence:.0%})",
    }
