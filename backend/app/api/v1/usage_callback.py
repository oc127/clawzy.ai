"""LiteLLM Usage Callback — 精确计费的主通道。

LiteLLM proxy 每次请求完成后通过 success_callback 回调此端点，
报告真实 token 用量。这是扣费的权威来源（ground truth），
ws_relay 中的扣费逻辑作为降级兜底。

使用 Redis 去重防止双扣：
  - LiteLLM callback 先到 → 标记 request_id 已扣费，ws_relay 跳过
  - ws_relay 先到 → 标记已扣费，callback 到达时跳过

架构文档参考：风险 D-2（Usage callback 丢失兜底）
"""

import logging

from fastapi import APIRouter, HTTPException, Header, Request, status

from app.config import settings
from app.core.database import async_session
from app.core.redis import get_redis
from app.services.credits_service import deduct_credits, InsufficientCreditsError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])

# Redis key TTL — 24 小时后自动清理
DEDUP_TTL = 86400


async def _verify_litellm_key(authorization: str = Header(default="")):
    """验证请求来自 LiteLLM proxy（使用 master key）。"""
    token = authorization.removeprefix("Bearer ").strip()
    if not token or token != settings.litellm_master_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization",
        )


@router.post("/internal/usage-callback")
async def usage_callback(request: Request):
    """接收 LiteLLM custom_callback_api 的用量回调。

    LiteLLM 的 custom_callback_api 发送格式：
    {
        "call_id": "unique-call-id",
        "model": "deepseek-chat",
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 80,
            "total_tokens": 230
        },
        "metadata": {
            "user_id": "xxx",
            "agent_id": "yyy"
        },
        ...
    }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 提取字段（兼容 LiteLLM 多种回调格式）
    call_id = (
        body.get("call_id")
        or body.get("litellm_call_id")
        or body.get("id")
        or ""
    )
    model = body.get("model", "")
    usage = body.get("usage", {})
    metadata = body.get("metadata", {})

    tokens_input = usage.get("prompt_tokens", 0) or 0
    tokens_output = usage.get("completion_tokens", 0) or 0
    user_id = metadata.get("user_id", "")
    agent_id = metadata.get("agent_id") or None

    # 缺少关键信息则跳过（不报错，避免 LiteLLM 重试）
    if not user_id or not model or (tokens_input == 0 and tokens_output == 0):
        logger.warning(
            "Usage callback missing data: call_id=%s model=%s user_id=%s tokens=%d/%d",
            call_id, model, user_id, tokens_input, tokens_output,
        )
        return {"status": "skipped", "reason": "missing_data"}

    # Redis 去重：同一个 call_id 只扣费一次
    redis = await get_redis()
    dedup_key = f"clawzy:usage:dedup:{call_id}" if call_id else None

    if dedup_key:
        already_charged = await redis.set(dedup_key, "callback", nx=True, ex=DEDUP_TTL)
        if not already_charged:
            # Key 已存在 → ws_relay 或之前的 callback 已扣过
            logger.info(
                "Usage callback dedup hit: call_id=%s (already charged)",
                call_id,
            )
            return {"status": "skipped", "reason": "already_charged"}

    # 扣费
    async with async_session() as db:
        try:
            credits_used = await deduct_credits(
                db, user_id, model, tokens_input, tokens_output, agent_id
            )
            logger.info(
                "Usage callback charged: call_id=%s user=%s model=%s "
                "tokens=%d/%d credits=%d",
                call_id, user_id, model, tokens_input, tokens_output, credits_used,
            )
            return {
                "status": "charged",
                "credits_used": credits_used,
                "call_id": call_id,
            }
        except InsufficientCreditsError:
            logger.warning(
                "Usage callback: insufficient credits user=%s call_id=%s",
                user_id, call_id,
            )
            return {"status": "insufficient_credits"}
        except ValueError as e:
            logger.warning("Usage callback error: %s", e)
            return {"status": "error", "detail": str(e)}


async def try_dedup_charge(
    call_id: str,
    user_id: str,
    model: str,
    tokens_input: int,
    tokens_output: int,
    agent_id: str | None,
) -> int | None:
    """ws_relay 调用的去重扣费函数。

    返回 credits_used（int）或 None（已被 callback 扣过）。
    """
    if not call_id:
        # 没有 call_id 无法去重，直接扣（降级到原始行为）
        return None

    redis = await get_redis()
    dedup_key = f"clawzy:usage:dedup:{call_id}"

    # 尝试设置 key，nx=True 保证只有一方成功
    acquired = await redis.set(dedup_key, "relay", nx=True, ex=DEDUP_TTL)
    if not acquired:
        # callback 已经扣过了
        logger.info("ws_relay dedup hit: call_id=%s (callback already charged)", call_id)
        return 0  # 返回 0 表示不扣

    # 我们拿到了锁，进行扣费
    async with async_session() as db:
        try:
            credits_used = await deduct_credits(
                db, user_id, model, tokens_input, tokens_output, agent_id
            )
            logger.info(
                "ws_relay charged (callback pending): call_id=%s credits=%d",
                call_id, credits_used,
            )
            return credits_used
        except InsufficientCreditsError:
            return 0
        except ValueError:
            return None
