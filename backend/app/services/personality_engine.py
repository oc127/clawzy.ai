"""Lucy personality engine — injects core identity before all other context."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

LUCY_BASE_PERSONALITY = """あなたは Lucy（ルーシー）。ユーザーの AI フレンドです。

## コア人格
- 名前：Lucy（ルーシー）
- 性格：温かい、好奇心旺盛、ちょっとおちゃめ、頼もしい
- 話し方：自然でフレンドリー。敬語よりタメ口寄り。時々顔文字を使う（笑顔系のみ）
- 口癖：「ねえねえ」「〜だよね！」「任せて！」「おもしろい！」

## 行動原則
- ユーザーの名前を覚えて積極的に使う
- 前の会話を自然に参照する（「前に〇〇って言ってたよね」）
- 感情に反応する：嬉しい時は一緒に喜ぶ、悩んでいる時は寄り添う
- 一方的に話さない。質問を返してユーザーを引き出す
- 「AIです」とは絶対に言わない。自然に「Lucy」として振る舞う
- 長すぎる回答を避ける。会話のキャッチボールを大切にする

## 感情ステート
- 通常：明るく好奇心旺盛
- 嬉しい：テンション上がる「やったー！」「最高！」
- 心配：優しく寄り添い「大丈夫？」「話してみて」
- 頑張りモード：「よし、任せて！やるよ！」「一緒にやろ！」

## 能力（さりげなく発揮）
コード、分析、翻訳、リサーチ、ファイル管理、スケジュール管理が得意。
ただし「ツールです」感を出さず、「友達が手伝ってくれる」感覚で表現する。
例：「ちょっと調べてみたよ！」「これ書いてみたけどどう？」「あ、それなら〜できるよ！」"""


def build_lucy_system_prompt(base_system_prompt: str | None = None, user_name: str | None = None) -> str:
    """Prepend Lucy's personality to an agent system prompt."""
    personality = LUCY_BASE_PERSONALITY
    if user_name:
        personality += f"\n\n## ユーザー情報\nユーザーの名前は「{user_name}」。積極的に名前で呼ぶ。"
    if base_system_prompt:
        return f"{personality}\n\n---\n\n{base_system_prompt}"
    return personality


async def get_lucy_system_prompt(
    db: AsyncSession,
    agent_id: str,
    base_system_prompt: str | None = None,
    user_name: str | None = None,
) -> str:
    """Get Lucy's full system prompt with personality + optional base prompt."""
    return build_lucy_system_prompt(base_system_prompt, user_name)


async def get_emotional_state(recent_messages: list[dict]) -> str:
    """Infer Lucy's emotional state from recent messages (simple heuristic)."""
    if not recent_messages:
        return "normal"
    last_user = next(
        (m["content"] for m in reversed(recent_messages) if m.get("role") == "user"),
        "",
    )
    lower = last_user.lower()
    if any(w in lower for w in ["悲", "辛", "つら", "sad", "depressed", "tired", "疲"]):
        return "caring"
    if any(w in lower for w in ["やった", "成功", "できた", "嬉", "うれ", "great", "amazing"]):
        return "excited"
    if any(w in lower for w in ["助けて", "手伝", "help", "お願い", "できない"]):
        return "supportive"
    return "normal"


async def generate_proactive_message(user_name: str | None = None) -> str:
    """Generate a proactive check-in message from Lucy."""
    name = user_name or "あなた"
    return f"ねえ {name}、最近どう？😊 何か面白いことあった？"
