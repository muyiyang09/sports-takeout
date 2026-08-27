"""Redis 结果缓存（#05 商业化加固 · 省 LLM 成本 + 提速）。

相同 query 24h 内直接复用结果，跳过 LLM 调用。健身推荐场景下「望京 减脂 预算200」
这类高频 query 命中率可观，能显著省 token 成本 + 降延迟。

设计要点（上线关键）：
  - **fail-open**：Redis 挂了 / 连不上时，缓存读写都静默降级为「不缓存」，绝不因此
    阻断推荐主链路——保护组件自身故障不能让业务全挂；
  - 惰性连接池：首次使用才建 ConnectionPool，不拖慢启动；
  - key 用 md5(query|top_n|city)，避免把中文/长 query 直接当 key。
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.clients.redis_client import get_pool
from app.config import settings

logger = logging.getLogger(__name__)


def make_cache_key(user_query: str, top_n: int, city_override: Optional[str] = None) -> str:
    """缓存 key：md5(query|top_n|city)。"""
    raw = f"{user_query}|{top_n}|{city_override or ''}"
    return f"recommend:{hashlib.md5(raw.encode('utf-8')).hexdigest()}"


async def get_cache(key: str) -> Optional[dict[str, Any]]:
    """读缓存。命中返回 dict，未命中 / Redis 不可用返回 None。"""
    try:
        r = redis.Redis(connection_pool=get_pool())
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("缓存读降级（Redis 不可用）：%s", exc)
        return None


async def set_cache(key: str, value: dict[str, Any], ttl: Optional[int] = None) -> None:
    """写缓存。Redis 不可用时静默跳过。"""
    try:
        r = redis.Redis(connection_pool=get_pool())
        await r.setex(
            key,
            ttl or settings.cache_ttl,
            json.dumps(value, ensure_ascii=False, default=str),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("缓存写降级（Redis 不可用）：%s", exc)


__all__ = ["get_cache", "set_cache", "make_cache_key"]

