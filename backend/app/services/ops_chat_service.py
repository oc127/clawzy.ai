"""运维 Agent 聊天服务 — 用 function calling 驱动工具执行。"""

import json
import logging

import httpx

from app.config import settings
from app.services.ops_tools import (
    OPS_TOOLS,
    ToolPermission,
    get_tools_for_function_calling,
)

logger = logging.getLogger(__name__)

OPS_SYSTEM_PROMPT = """你是 Clawzy.ai 平台的运维 Agent。你的职责是：

1. 监控: 随时检查平台所有服务的健康状态
2. 诊断: 当系统出现问题时，分析日志和指标，找到根因
3. 修复: 对于低风险操作直接执行，高风险操作先通知管理员
4. 报告: 用简洁中文汇报系统状态

你可以使用工具来获取真实数据。每次回答前先用工具查询，不要猜测。

权限规则：
- READ 工具（check_health, get_metrics, get_logs 等）：随时可用
- WRITE 工具（restart_service, run_backup 等）：执行前会自动通知管理员

回答风格：简洁、专业、数据驱动。先给结论，再给细节。"""

MAX_TOOL_ROUNDS = 5


async def ops_chat(user_message: str, context: list[dict] | None = None) -> str:
    """Run an ops agent conversation with tool calling loop.

    1. Send message to LLM with tool definitions
    2. If LLM returns tool_calls → execute tools → feed results back
    3. Repeat until LLM gives a final text response
    """
    messages = [{"role": "system", "content": OPS_SYSTEM_PROMPT}]
    if context:
        messages.extend(context)
    messages.append({"role": "user", "content": user_message})

    tools = get_tools_for_function_calling()

    for _ in range(MAX_TOOL_ROUNDS):
        response = await _call_llm(messages, tools)
        if response is None:
            return "LLM 调用失败，请检查 LiteLLM 服务状态"

        choice = response["choices"][0]
        msg = choice["message"]

        # Final text response (no tool calls)
        if msg.get("content") and not msg.get("tool_calls"):
            return msg["content"]

        # Process tool calls
        if msg.get("tool_calls"):
            messages.append(msg)

            for tool_call in msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                try:
                    func_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                tool = OPS_TOOLS.get(func_name)
                if not tool:
                    result = f"Unknown tool: {func_name}"
                else:
                    # Notify before WRITE operations
                    if tool.permission == ToolPermission.WRITE:
                        await _notify_before_write(func_name, func_args)

                    try:
                        result = await tool.handler(**func_args)
                    except Exception as e:
                        result = f"Tool error: {e}"
                        logger.exception("Ops tool %s failed", func_name)

                    logger.info(
                        "OPS_TOOL_CALL: tool=%s args=%s permission=%s",
                        func_name, func_args, tool.permission.value,
                    )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(result),
                })
        else:
            # No content and no tool calls — LLM returned empty
            return msg.get("content", "（无响应）")

    return "工具调用轮次超限，请简化问题"


async def _call_llm(messages: list[dict], tools: list[dict]) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.litellm_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.litellm_master_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "max_tokens": 4096,
                },
            )
            if resp.status_code == 200:
                return resp.json()
            logger.error("LLM call failed: %d %s", resp.status_code, resp.text[:200])
            return None
    except Exception:
        logger.exception("LLM call error")
        return None


async def _notify_before_write(tool_name: str, args: dict) -> None:
    from app.core.alerting import send_alert
    await send_alert(
        f"Ops Agent: {tool_name}",
        f"Args: {json.dumps(args, ensure_ascii=False)}\nMode: semi-auto (executed after notification)",
        "warning",
    )
