"""断线 fallback 服务 — 龙虾不在时的友好回复。

当 LiteLLM/模型 API 不可用、容器崩溃、或其他异常时，
不要让用户看到冷冰冰的错误，而是用预设的友好回复保持对话。
"""

import random

# 模型不可用时的回复（像客服一样回应用户）
MODEL_UNAVAILABLE_REPLIES = [
    "抱歉，我的大脑暂时有点迷糊 🤯 工程师们正在修复，稍等一下就好啦～",
    "哎呀，我的思考能力暂时掉线了 😅 别担心，很快就恢复！你可以先休息一下～",
    "不好意思！我现在有点反应不过来 🦞💤 系统正在紧急处理，请稍后再试哦",
    "我的大脑正在充能中 ⚡ 大概需要几分钟，一会儿就满血复活！",
]

# 容器/Agent 不可用时的回复
AGENT_DOWN_REPLIES = [
    "我刚睡了一小觉 😴 正在快速醒来，请稍等片刻...",
    "我暂时不太舒服 🤒 工程师正在帮我恢复，很快就好！",
    "我正在重启中 🔄 请稍等 30 秒，马上就回来陪你！",
]

# 网络/超时问题时的回复
NETWORK_ERROR_REPLIES = [
    "信号不太好的样子 📡 我正在尝试重新连接，请稍等～",
    "网络打了个喷嚏 🤧 我正在重新接入，稍后再发一次试试？",
]

# 积分不足时的回复
NO_CREDITS_REPLIES = [
    "你的能量用完啦 ⚡ 去充充能量我们就能继续聊了！",
    "能量不足了 😢 升级套餐或者充值能量，我们再继续？",
]

# 被限流时的回复
RATE_LIMITED_REPLIES = [
    "你打字太快啦 😆 让我缓缓，稍后再说～",
    "慢一点慢一点 🦞 我也需要呼吸的！等几秒再发吧～",
]


def get_fallback_reply(error_type: str) -> str:
    """根据错误类型返回一条友好的 fallback 回复。"""
    pool = {
        "model_error": MODEL_UNAVAILABLE_REPLIES,
        "timeout": MODEL_UNAVAILABLE_REPLIES,
        "connection_error": NETWORK_ERROR_REPLIES,
        "empty_response": MODEL_UNAVAILABLE_REPLIES,
        "agent_down": AGENT_DOWN_REPLIES,
        "insufficient_credits": NO_CREDITS_REPLIES,
        "rate_limited": RATE_LIMITED_REPLIES,
    }.get(error_type, MODEL_UNAVAILABLE_REPLIES)

    return random.choice(pool)


# 模型切换时的回复
MODEL_SWITCHED_REPLIES = [
    "刚换了个大脑思考了一下 🧠 答案来啦！",
    "我用备用大脑帮你想了想 🤔 结果如下～",
]


def get_model_switched_message() -> str:
    """当自动切换到备用模型时的友好通知。"""
    return random.choice(MODEL_SWITCHED_REPLIES)


def get_reconnecting_message() -> str:
    """WebSocket 断线后重连时发给用户的第一条消息。"""
    return random.choice([
        "我回来啦！刚才断开了一下，现在没问题了 🦞✨",
        "重新连上了！之前说到哪了？我们继续吧 😊",
        "网络恢复了！我还在这儿，你想聊什么？",
    ])
