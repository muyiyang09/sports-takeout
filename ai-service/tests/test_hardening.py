"""商业化加固（#05）单元测试：熔断器 / token 估算 / 缓存 key / 错误码。

纯函数 + 无 LLM/DB/Redis 依赖，可直接离线跑。

运行：
    cd ai-service
    ./.venv/Scripts/python.exe -m pytest tests/test_hardening.py -q
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("AI_MOCK", "1")

from app.clients.cache import make_cache_key  # noqa: E402
from app.clients.circuit_breaker import CircuitBreaker, CircuitState  # noqa: E402
from app.core.exceptions import (  # noqa: E402
    LLMUnavailableError,
    RateLimitError,
    TokenBudgetExceededError,
)
from app.middleware.token_budget import estimate_tokens  # noqa: E402


# ---------------------------------------------------------------------------
# Token 估算
# ---------------------------------------------------------------------------
def test_estimate_tokens_cjk():
    # 中文 1 字符 ≈ 1 token（+1 兜底）
    assert estimate_tokens("减脂塑形") == 5


def test_estimate_tokens_english():
    # 英文 4 字符 ≈ 1 token（+1 兜底）
    assert estimate_tokens("abcd") == 2


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 1


# ---------------------------------------------------------------------------
# 缓存 key
# ---------------------------------------------------------------------------
def test_make_cache_key_stable_and_distinct():
    assert make_cache_key("减脂", 3, None) == make_cache_key("减脂", 3, None)
    assert make_cache_key("减脂", 3, None) != make_cache_key("增肌", 3, None)
    assert make_cache_key("减脂", 3, "北京市") != make_cache_key("减脂", 3, None)


# ---------------------------------------------------------------------------
# 熔断器
# ---------------------------------------------------------------------------
def test_circuit_breaker_opens_and_fails_fast():
    cb = CircuitBreaker(fail_threshold=2, reset_timeout=60)
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            asyncio.run(cb.call(flaky))

    assert cb.state == CircuitState.OPEN
    assert calls["n"] == 2

    # OPEN 状态：快速失败，不再真正调用 fn
    with pytest.raises(RuntimeError):
        asyncio.run(cb.call(flaky))
    assert calls["n"] == 2  # 没再调 flaky


def test_circuit_breaker_recovers_after_timeout():
    cb = CircuitBreaker(fail_threshold=1, reset_timeout=60)

    async def flaky():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        asyncio.run(cb.call(flaky))
    assert cb.state == CircuitState.OPEN

    # 模拟超时已过：半开试探成功 → 恢复闭合
    cb.last_fail_time = 0.0

    async def ok():
        return "ok"

    assert asyncio.run(cb.call(ok)) == "ok"
    assert cb.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# 错误码 → HTTP 状态
# ---------------------------------------------------------------------------
def test_exception_http_status():
    assert RateLimitError().http_status == 429
    assert TokenBudgetExceededError().http_status == 429
    assert LLMUnavailableError().http_status == 503


def test_exception_code_and_msg():
    e = RateLimitError()
    assert e.code == "AI_RATE_LIMIT"
    assert e.msg
