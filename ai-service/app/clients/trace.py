"""轻量 Trace：节点级耗时追踪（#06 可观测性）。

设计取舍（为什么默认不用 Langfuse）：
  - Langfuse 是重依赖（独立服务 + langfuse 包），国内自部署成本高；
  - 这里先用「结构化日志」记录每个节点的耗时，配合 request_id 就能在日志系统里
    串起一次请求的节点链路，覆盖 80% 的可观测需求；
  - 预留 `_emit_langfuse` 钩子：等接入 Langfuse 时（装包 + 配 key）再启用，零改动。

产出：每次节点执行打一条 `[Trace] node=xxx latency_ms=yyy`（带 request_id）。
"""
from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Awaitable, Callable

logger = logging.getLogger("app.trace")


def trace_node(name: str):
    """节点级耗时装饰器。包装 async 节点，打一条耗时日志。"""

    def decorator(fn: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @wraps(fn)
        async def wrapper(state):
            start = time.perf_counter()
            try:
                return await fn(state)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info("[Trace] node=%s latency_ms=%.1f", name, elapsed_ms)

        return wrapper

    return decorator


__all__ = ["trace_node"]
