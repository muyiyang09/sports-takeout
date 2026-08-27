"""审计日志（#05 商业化加固 · 合规/成本溯源）。

所有 LLM / 工具调用写入 MySQL `ai_audit_log` 表，用于：
  1. 合规审计：谁、何时、用什么模型、花了多少 token；
  2. 成本溯源：按 user_id / request_id 回溯 token 消耗；
  3. 问题定位：请求失败时能查到当时的 prompt/response/error。

设计要点：
  - **旁路写入、绝不阻断主流程**：审计写失败只告警、不影响推荐响应；
  - prompt/response 截断到 1000 字符，避免日志表被长 prompt 撑爆；
  - 依赖 `sql/ai_audit_log.sql` 先建表；表未建时写失败会告警（生产前必须建）。
"""
from __future__ import annotations

import logging
from uuid import uuid4

from app.clients.db import aexecute

logger = logging.getLogger(__name__)

# prompt/response 只留前 1000 字符，够溯源又不撑爆表
_MAX_TEXT = 1000


async def log_audit(
    *,
    user_id: str,
    request_id: str,
    action: str,                 # "llm_call" / "tool_call" / "graph_invoke"
    model: str | None = None,
    prompt: str | None = None,
    response: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_ms: int = 0,
    success: bool = True,
    error: str | None = None,
) -> None:
    """异步写一条审计日志。失败只告警，不抛异常（旁路）。"""
    sql = (
        "INSERT INTO ai_audit_log "
        "(id, user_id, request_id, action, model, prompt, response, "
        " input_tokens, output_tokens, duration_ms, success, error, created_at) "
        "VALUES (:id, :user_id, :request_id, :action, :model, :prompt, :response, "
        "        :input_tokens, :output_tokens, :duration_ms, :success, :error, NOW())"
    )
    params = {
        "id": str(uuid4()),
        "user_id": user_id,
        "request_id": request_id,
        "action": action,
        "model": model,
        "prompt": (prompt or "")[:_MAX_TEXT] or None,
        "response": (response or "")[:_MAX_TEXT] or None,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "success": 1 if success else 0,
        "error": error,
    }
    try:
        await aexecute(sql, params)
    except Exception as exc:  # noqa: BLE001
        logger.warning("审计日志写入失败（不影响主流程，生产前需执行 sql/ai_audit_log.sql）：%s", exc)


__all__ = ["log_audit"]
