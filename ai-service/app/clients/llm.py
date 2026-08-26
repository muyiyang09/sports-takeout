"""LLM 客户端：基于 LiteLLM 的统一封装。
用 OpenAI 兼容模式 + BaseChatModel 契约（参考经验 1674242），避免把「供应商选择」
和「Agent/工具编排」耦合：换模型只改 .env 的 LLM_MODEL/LLM_API_KEY，上层代码 0 改动。
"""
from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable
from typing import Any, Optional, Type, TypeVar, cast

from litellm import acompletion, completion
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# =============================================================================
# 通用参数：所有 LLM 请求走同一组配置，保证行为一致
# =============================================================================
def _common_kwargs() -> dict[str, Any]:
    kw: dict[str, Any] = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "timeout": settings.llm_timeout,
        "num_retries": settings.llm_max_retries,
    }
    if settings.llm_api_key:
        kw["api_key"] = settings.llm_api_key
    if settings.llm_base_url:
        kw["api_base"] = settings.llm_base_url
    return kw


def _strip_text(text: Any) -> str:
    return (str(text) if text is not None else "").strip()


# =============================================================================
# 1. 普通文本生成
# =============================================================================
def chat(messages: Iterable[dict[str, str]]) -> str:
    """同步调用 LLM，返回纯文本回答。"""
    msgs = [
        {"role": m["role"], "content": _strip_text(m.get("content", ""))}
        for m in messages
    ]
    resp = completion(messages=msgs, **_common_kwargs())
    try:
        return _strip_text(resp.choices[0].message.content)
    except (AttributeError, IndexError, KeyError) as exc:
        logger.error("LLM 返回结构异常: %s | resp=%s", exc, resp)
        raise RuntimeError(f"LLM 返回结构异常：{exc}") from exc


async def achat(messages: Iterable[dict[str, str]]) -> str:
    msgs = [
        {"role": m["role"], "content": _strip_text(m.get("content", ""))}
        for m in messages
    ]
    resp = await acompletion(messages=msgs, **_common_kwargs())
    try:
        return _strip_text(resp.choices[0].message.content)
    except (AttributeError, IndexError, KeyError) as exc:
        logger.error("LLM 返回结构异常: %s | resp=%s", exc, resp)
        raise RuntimeError(f"LLM 返回结构异常：{exc}") from exc


# =============================================================================
# 2. 结构化输出（Pydantic）—— 带结构适配层（经验 100036121）
# =============================================================================
def normalize_for_pydantic(raw: Any, expected_root_type: Type[T]) -> dict[str, Any]:
    """把 LLM 可能漂移的输出收敛成 schema 期望的 dict。

    核心规则（来自经验 100036121）：
      1) 顶层 list → 自动包进已知承载字段(candidates/items...)；
      2) 字段名别名/大小写漂移 → 按映射表收敛到 schema 标准字段名；
      3) 缺失 list 字段 → 填 []，避免必填校验硬失败。
    """
    # 规则 1：顶层 list 先包一层
    if isinstance(raw, list):
        fields = set(expected_root_type.model_fields.keys())
        for key in ("candidates", "coach_ids", "items", "results", "data", "top_coaches"):
            if key in fields:
                raw = {key: raw}
                break
        else:
            raw = raw[0] if raw else {}

    if not isinstance(raw, dict):
        raise ValueError(
            f"归一化失败：raw={type(raw).__name__} 无法转 dict，raw 前 200={str(raw)[:200]!r}"
        )

    # 规则 2：字段别名映射（教练推荐相关常见别名）
    alias_map: dict[str, tuple[str, ...]] = {
        "coach_ids": ("coachIdList", "coach_ids", "coachId", "coaches", "coach"),
        "recommend_reason": ("recommend_reason", "reason", "why", "summary", "reasoning"),
        "specialization_tags": ("tags", "labels", "specialization", "skills", "擅长领域"),
        "specialization": ("specialization", "speciality", "domain", "targets", "目标"),
        "district": ("district", "area", "region", "neighborhood", "区域"),
        "time_slot": ("time_slot", "slot", "schedule", "appointmentTime", "时段"),
        "city_name": ("city_name", "city", "城市"),
        "max_price": ("max_price", "priceMax", "budget", "预算"),
        "min_rating": ("min_rating", "ratingMin", "评分"),
        "level": ("level", "level_required", "等级"),
    }
    fields = set(expected_root_type.model_fields.keys())
    normalized: dict[str, Any] = {}
    for canonical, aliases in alias_map.items():
        if canonical in fields and canonical not in raw:
            for alias in aliases:
                if alias in raw and raw[alias] is not None:
                    normalized[canonical] = raw[alias]
                    break
    # 其他字段原样 copy
    normalized.update({k: v for k, v in raw.items() if k not in normalized})

    # 规则 3：缺失 list 类型字段默认 []
    for name, field_info in expected_root_type.model_fields.items():
        if name in normalized:
            continue
        annotation = str(field_info.annotation)
        if annotation.startswith("list") or "list[" in annotation or "List[" in annotation:
            normalized[name] = []
    return normalized


def chat_structured(messages: Iterable[dict[str, str]], output_schema: Type[T]) -> T:
    """结构化输出：JSON Schema 提示词 + 代码侧归一化 + Pydantic 校验。"""
    schema_json = output_schema.model_json_schema()
    system_with_schema = (
        "你是一个严格的 JSON 生成器。只根据给定的 JSON Schema 输出结果，"
        "不要有任何解释、Markdown、反引号、额外字符或嵌套代码块。\n"
        f"JSON Schema:\n{json.dumps(schema_json, ensure_ascii=False)}\n"
        "直接输出满足 schema 的 JSON object。"
    )
    msgs = [{"role": "system", "content": system_with_schema}, *list(messages)]
    raw_text = chat(msgs)

    parsed: Any
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = raw_text.strip().removeprefix("```json").removeprefix("```JSON").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(
                "结构化 JSON 解析失败。原始前 400 字=%s | exc=%s",
                raw_text[:400],
                exc,
            )
            raise RuntimeError(
                f"LLM 输出非合法 JSON：{exc}。前400字={raw_text[:400]}"
            ) from exc

    data = normalize_for_pydantic(parsed, output_schema)
    try:
        return output_schema.model_validate(data)
    except ValidationError as exc:
        logger.error(
            "Pydantic 校验失败：normalized=%s | errors=%s",
            data,
            exc.errors(),
        )
        raise


# =============================================================================
# 3. Mock（离线 demo：没配 api_key 或 AI_MOCK=1 时自动走假数据）
# =============================================================================
def is_mock_mode() -> bool:
    if os.environ.get("AI_MOCK", "").lower() in {"1", "true", "yes", "on"}:
        return True
    return not settings.llm_api_key


def mock_structured(output_schema: Type[T], fallback: Optional[T] = None) -> T:
    if fallback is not None:
        return fallback
    defaults: dict[str, Any] = {}
    for name, field_info in output_schema.model_fields.items():
        if field_info.default is not None:
            defaults[name] = field_info.default
        elif "list[" in str(field_info.annotation):
            defaults[name] = []
    return cast(T, output_schema.model_construct(**defaults))
