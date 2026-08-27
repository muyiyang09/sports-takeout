"""FastAPI 服务入口：对外暴露教练推荐 HTTP API，供 Java 后端和小程序调用。

#05 商业化加固后：
  - 全链路异步（async 端点 + ainvoke + acompletion）；
  - /v1 版本前缀 + liveness(/healthz)/readiness(/readyz) 分离；
  - 结构化 JSON 日志 + request_id 贯穿 + 全局异常（错误码）；
  - 三级限流 + Token 预算 + 结果缓存 + 审计日志 + 优雅停机。

启动：
    cd ai-service
    python -m pip install -e .      # 首次：装依赖
    cp .env.example .env            # 填 LLM_API_KEY（不填也能跑 mock）
    python -m app.main              # 或：uvicorn app.main:app --host 0.0.0.0 --port 18000
"""
from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional
from uuid import uuid4

import redis.asyncio as redis
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.clients import redis_client
from app.clients.cache import get_cache, make_cache_key, set_cache
from app.clients.db import aexecute, get_engine, is_db_available
from app.clients.llm import is_mock_mode
from app.config import settings
from app.core import hitl_state, metrics
from app.core.audit import log_audit
from app.core.exceptions import (
    AIError,
    ConflictError,
    NotFoundError,
    UpstreamError,
    ValidationFailedError,
)
from app.core.logging import request_id_var, setup_logging
from app.core.safety import detect_injection
from app.graphs.cert_review import CERT_REVIEW_GRAPH
from app.graphs.recommend_coach import RECOMMEND_GRAPH
from app.graphs.review_summary import REVIEW_SUMMARY_GRAPH
from app.graphs.supervisor import route_query
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.token_budget import check_token_budget, estimate_tokens
from app.schemas.cert_review import CertReviewIn, CertReviewResult
from app.schemas.coach_recommend import RecommendResult
from app.schemas.review_summary import ReviewSummaryIn, ReviewSummaryResult

logger = logging.getLogger("app.main")


# =============================================================================
# HTTP 请求 / 响应契约
# =============================================================================
class RecommendCoachIn(BaseModel):
    user_query: str = Field(
        ..., min_length=1, max_length=500, description="用户自然语言，如 '望京 预算200 产后恢复 周末'"
    )
    city_code_override: Optional[str] = Field(
        default=None, description="可选：小程序端已知用户城市时，强制覆盖 LLM 抽取结果"
    )
    top_n: int = Field(default=3, ge=1, le=5, description="返回教练数量（1~5）")


class FeedbackIn(BaseModel):
    """用户对推荐结果的反馈（点赞/点踩/下单），用于在线 Eval 回流。"""

    request_id: str = Field(..., description="对应推荐请求的 request_id（关联审计/日志）")
    action: str = Field(..., description="用户行为：like / dislike / order")
    coach_id: Optional[int] = Field(default=None, description="被点击/下单的教练 ID")
    feedback: Optional[str] = Field(default=None, description="补充文字反馈")


class ChatIn(BaseModel):
    """统一 AI 入口请求（Supervisor 路由）。"""

    query: str = Field(..., min_length=1, max_length=500, description="用户自由文本")
    thread_id: Optional[str] = Field(default=None, description="会话 ID（可选）")


class ResumeIn(BaseModel):
    """HITL 审核单恢复请求。"""

    action: str = Field(..., description="管理员决定：approve / reject")


# =============================================================================
# 生命周期：启动初始化 + 优雅停机
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(logging.INFO if settings.service_env != "dev" else logging.DEBUG)
    logger.info(
        "AI 服务启动：env=%s port=%s LLM=%s mock_mode=%s",
        settings.service_env, settings.service_port, settings.llm_model, is_mock_mode(),
    )

    # DB 灾备表建表（幂等，失败不阻断启动——Checkpointer 仍可用，只是 DB 兜底层会降级）
    if settings.checkpointer_backend == "redis" and settings.checkpoint_db_fallback:
        try:
            from app.core import session_store
            await session_store.ensure_table()
            logger.info("[SessionStore] ai_session_state 表已就绪（DB 灾备层激活）")
        except Exception as exc:  # noqa: BLE001
            logger.warning("[SessionStore] 建表失败（不影响启动，DB 兜底层降级为不可用）：%s", exc)

    yield
    # 优雅停机：清空连接池（uvicorn --timeout-graceful-shutdown 已处理在飞请求层）
    logger.info("AI 服务停止：关闭 DB 连接池 + Redis 连接池")
    try:
        get_engine().dispose()
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB 连接池关闭失败：%s", exc)
    await redis_client.close()


app = FastAPI(
    title="Sports Takeout · AI Service",
    description="体育外卖 · AI 微服务：教练智能推荐（LangGraph + LiteLLM + Pydantic）",
    version="0.2.0",
    lifespan=lifespan,
)

# 中间件：后添加者更外层（先处理请求）。顺序：CORS(最外) → request_id → 限流(最内)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 全局异常处理：把 AIError 统一转成 {code, msg, request_id}，不泄露内部栈
# =============================================================================
@app.exception_handler(AIError)
async def ai_error_handler(request: Request, exc: AIError) -> JSONResponse:
    metrics.incr("error_total")
    if exc.detail:
        logger.warning("AIError[%s] %s | detail=%s", exc.code, exc.msg, exc.detail)
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "msg": exc.msg, "request_id": request_id_var.get()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：未预期的异常也返回结构化错误码，绝不裸 500 + 堆栈。"""
    metrics.incr("error_total")
    logger.exception("未预期异常：%s", exc)
    return JSONResponse(
        status_code=500,
        content={"code": "AI_INTERNAL", "msg": "AI 服务内部错误", "request_id": request_id_var.get()},
    )


# =============================================================================
# 健康探针：liveness / readiness 分离（K8s 滚动更新必备）
# =============================================================================
@app.get("/healthz", tags=["System"], summary="Liveness：进程是否活着（不查依赖）")
async def healthz() -> dict[str, object]:
    return {"ok": True, "env": settings.service_env, "mock_mode": is_mock_mode()}


@app.get("/readyz", tags=["System"], summary="Readiness：是否准备好接流量（查 DB/Redis/LLM）")
async def readyz() -> dict[str, object]:
    checks: dict[str, str] = {}

    # DB
    try:
        db_ok = await asyncio.to_thread(is_db_available)
        checks["db"] = "ok" if db_ok else "down"
    except Exception:  # noqa: BLE001
        checks["db"] = "down"

    # Redis
    try:
        r = redis.Redis(connection_pool=redis_client.get_pool())
        await r.ping()
        checks["redis"] = "ok"
    except Exception:  # noqa: BLE001
        checks["redis"] = "down"

    # LLM：mock 模式视为可用（离线兜底）
    checks["llm"] = "mock" if is_mock_mode() else "ok"

    ready = all(v in ("ok", "mock") for v in checks.values())
    return {"ok": ready, "checks": checks}


@app.get("/metrics", tags=["System"], summary="Prometheus 指标导出")
async def metrics_endpoint() -> Response:
    """导出 Prometheus 文本格式指标（llm/tool/cache/error/latency）。"""
    return Response(content=metrics.render(), media_type="text/plain; version=0.0.4")


# =============================================================================
# 业务接口：教练推荐（/v1 前缀，异步）
# =============================================================================
@app.post(
    "/v1/ai/recommend-coach",
    tags=["AI"],
    summary="教练智能推荐（自然语言 → Top N 教练 + 理由）",
    response_model=RecommendResult,
)
async def recommend_coach(
    payload: RecommendCoachIn,
    request: Request,
    x_user_id: Optional[str] = Header(default=None),
) -> RecommendResult:
    user_id = x_user_id or "anon"
    request_id = request_id_var.get()
    query = payload.user_query.strip()
    if not query:
        raise ValidationFailedError("user_query 不能为空")

    # 注入检测（只告警 + 计数，不粗暴拒绝——推荐是低风险场景）
    if detect_injection(query):
        metrics.incr("injection_detected_total")
        logger.warning("[Safety] 检测到疑似提示词注入：%s", query[:100])

    # 1. Token 预算（fail-open：Redis 挂了直接放过）
    await check_token_budget(user_id, estimate_tokens(query))

    # 2. 结果缓存（相同 query 24h 复用，跳过 LLM）
    cache_key = make_cache_key(query, payload.top_n, payload.city_code_override)
    if settings.cache_enabled:
        cached = await get_cache(cache_key)
        if cached:
            metrics.incr("cache_hit_total")
            logger.info("[Cache] 命中，跳过 LLM：%s", query[:50])
            return RecommendResult.model_validate(cached)
        metrics.incr("cache_miss_total")

    # 3. 走 Graph（ainvoke）
    thread_id = f"anon-{uuid4().hex}"  # 单次推荐无 resume，唯一 id 避免跨请求状态累积
    state_in: dict[str, object] = {"user_query": query, "top_n": payload.top_n}
    if payload.city_code_override:
        state_in["city_code_override"] = payload.city_code_override

    start = time.perf_counter()
    try:
        state_out = await RECOMMEND_GRAPH.ainvoke(
            state_in, config={"configurable": {"thread_id": thread_id}}
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Graph 执行失败：query=%s", query)
        raise UpstreamError(f"Graph 执行失败：{exc!r}") from exc
    duration_ms = int((time.perf_counter() - start) * 1000)
    metrics.observe("graph_latency_ms", duration_ms)

    result_dict = state_out.get("result")
    if not result_dict:
        raise UpstreamError("Graph 返回缺 result 字段")
    result = RecommendResult.model_validate(result_dict)

    # 4. 写缓存 + 审计（旁路，不阻断响应）
    if settings.cache_enabled:
        await set_cache(cache_key, result.model_dump())
    asyncio.create_task(
        log_audit(
            user_id=user_id,
            request_id=request_id,
            action="graph_invoke",
            model=settings.llm_model,
            prompt=query,
            response=result.recommend_reason,
            input_tokens=estimate_tokens(query),
            output_tokens=estimate_tokens(result.recommend_reason),
            duration_ms=duration_ms,
            success=True,
        )
    )
    return result


@app.post("/v1/ai/feedback", tags=["AI"], summary="用户反馈回流（点赞/点踩/下单）")
async def feedback(payload: FeedbackIn, request: Request) -> dict[str, bool]:
    """把用户反馈写入 ai_eval_online 表，作为在线 Eval 集（真实 ground truth）。

    旁路写入：失败不阻断响应（反馈不应拖垮主流程），但生产前需建表。
    """
    user_id = request.headers.get("x-user-id", "anon")
    sql = (
        "INSERT INTO ai_eval_online "
        "(request_id, user_id, action, coach_id, feedback, created_at) "
        "VALUES (:request_id, :user_id, :action, :coach_id, :feedback, NOW())"
    )
    try:
        await aexecute(sql, {
            "request_id": payload.request_id,
            "user_id": user_id,
            "action": payload.action,
            "coach_id": payload.coach_id,
            "feedback": payload.feedback,
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("反馈写入失败（不影响主流程，生产前需执行 sql/ai_eval_online.sql）：%s", exc)
    return {"ok": True}


@app.post("/v1/ai/review-summary", response_model=ReviewSummaryResult, tags=["AI"],
          summary="评价摘要（教练优缺点 + 标签）")
async def review_summary(payload: ReviewSummaryIn, request: Request) -> ReviewSummaryResult:
    if not settings.review_summary_enabled:
        raise ValidationFailedError("评价摘要 Agent 未启用")
    thread_id = f"review-{payload.coach_id}-{uuid4().hex}"
    try:
        state_out = await REVIEW_SUMMARY_GRAPH.ainvoke(
            {"coach_id": payload.coach_id, "limit": payload.limit},
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("评价摘要执行失败：coach_id=%s", payload.coach_id)
        raise UpstreamError(f"评价摘要执行失败：{exc!r}") from exc
    return ReviewSummaryResult.model_validate(state_out["result"])


@app.post("/v1/ai/cert-review", tags=["AI"],
          summary="证书审核（OCR → 核验 → 风险评估；HITL 开启时返回 pending）")
async def cert_review(payload: CertReviewIn, request: Request):
    if not settings.cert_review_enabled:
        raise ValidationFailedError("证书审核 Agent 未启用")
    thread_id = f"cert-{payload.coach_id}-{uuid4().hex}"
    try:
        state_out = await CERT_REVIEW_GRAPH.ainvoke(
            {
                "coach_id": payload.coach_id,
                "cert_type": payload.cert_type,
                "cert_number": payload.cert_number,
                "holder_name": payload.holder_name,
                "image_url": payload.image_url,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("证书审核执行失败：coach_id=%s", payload.coach_id)
        raise UpstreamError(f"证书审核执行失败：{exc!r}") from exc

    # HITL 开启时：interrupt 暂停，返回 pending + thread_id，等管理员 resume
    if "__interrupt__" in state_out:
        await hitl_state.set_status(thread_id, hitl_state._PENDING)
        return {
            "status": "pending",
            "thread_id": thread_id,
            "interrupt": [i.get("value") if isinstance(i, dict) else str(i) for i in state_out["__interrupt__"]],
        }

    return CertReviewResult.model_validate(state_out["result"])


@app.post("/v1/ai/cert-review/{thread_id}/resume", tags=["AI"],
          summary="HITL 人工确认（approve / reject）")
async def resume_cert_review(thread_id: str, payload: ResumeIn) -> CertReviewResult:
    if not settings.hitl_enabled:
        raise ValidationFailedError("HITL 未启用")

    # 冲突检测：已处理过 / 已取消 → 拒绝重复 resume
    status = await hitl_state.get_status(thread_id)
    if hitl_state.is_terminal(status):
        raise ConflictError("该审核单已处理过")
    if status is None:
        raise NotFoundError("审核单不存在或已过期")

    try:
        state_out = await CERT_REVIEW_GRAPH.ainvoke(
            Command(resume={"action": payload.action}),
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("证书审核 resume 失败：thread_id=%s", thread_id)
        raise UpstreamError(f"证书审核 resume 失败：{exc!r}") from exc

    result = CertReviewResult.model_validate(state_out["result"])
    await hitl_state.set_status(thread_id, payload.action)
    return result


@app.post("/v1/ai/cert-review/{thread_id}/cancel", tags=["AI"],
          summary="HITL 取消审核单")
async def cancel_cert_review(thread_id: str) -> dict[str, object]:
    if not settings.hitl_enabled:
        raise ValidationFailedError("HITL 未启用")
    await hitl_state.set_status(thread_id, "cancelled")
    return {"ok": True, "thread_id": thread_id, "status": "cancelled"}


@app.post("/v1/ai/chat", tags=["AI"], summary="统一 AI 入口（Supervisor 路由）")
async def chat(payload: ChatIn, request: Request) -> dict[str, object]:
    """Supervisor 路由：推荐教练直接派发，评价/证书返回路由提示（走专用端点）。"""
    agent = await route_query(payload.query)
    if agent == "recommend_coach":
        state_out = await RECOMMEND_GRAPH.ainvoke(
            {"user_query": payload.query, "top_n": 3},
            config={"configurable": {"thread_id": payload.thread_id or f"chat-{uuid4().hex}"}},
        )
        return {"agent": agent, "result": RecommendResult.model_validate(state_out["result"]).model_dump()}
    return {"agent": agent, "hint": "请调用对应专用端点（/v1/ai/review-summary 或 /v1/ai/cert-review）"}


# =============================================================================
# 脚本模式：python -m app.main 时直接启动 uvicorn
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.service_env == "dev",
    )
