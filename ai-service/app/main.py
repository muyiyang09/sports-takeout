"""FastAPI 服务入口：对外暴露教练推荐 HTTP API，供 Java 后端和小程序调用。

启动：
    cd ai-service
    python -m pip install -e .      # 首次：装依赖
    cp .env.example .env            # 填 LLM_API_KEY（不填也能跑 mock）
    python -m app.main              # 或：uvicorn app.main:app --host 0.0.0.0 --port 18000 --reload

调用：
    curl -s -X POST http://127.0.0.1:18000/ai/recommend-coach \
         -H 'Content-Type: application/json' \
         -d '{"user_query": "我家住望京，预算 200 以内，想产后恢复，最好周末上午"}'
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.clients.llm import is_mock_mode
from app.config import settings
from app.graphs.recommend_coach import RECOMMEND_GRAPH
from app.schemas.coach_recommend import RecommendResult

# =============================================================================
# 日志
# =============================================================================
logging.basicConfig(
    level=logging.INFO if settings.service_env != "dev" else logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
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


# =============================================================================
# FastAPI App
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "🚀 AI 服务启动：env=%s port=%s LLM=%s mock_mode=%s",
        settings.service_env,
        settings.service_port,
        settings.llm_model,
        is_mock_mode(),
    )
    yield  # 在这里放 shutdown 钩子（如关 DB 连接）
    logger.info("🛑 AI 服务停止")


app = FastAPI(
    title="Sports Takeout · AI Service",
    description="体育外卖 · AI 微服务：教练智能推荐（LangGraph + LiteLLM + Pydantic）",
    version="0.1.0",
    lifespan=lifespan,
)

# 允许管理端前端 / 小程序开发者工具跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["System"], summary="健康检查")
def healthz() -> dict[str, object]:
    return {
        "ok": True,
        "env": settings.service_env,
        "mock_mode": is_mock_mode(),
        "llm_model": settings.llm_model,
    }


@app.post(
    "/ai/recommend-coach",
    tags=["AI"],
    summary="教练智能推荐（自然语言 → Top N 教练 + 理由）",
    response_model=RecommendResult,
)
def recommend_coach(payload: RecommendCoachIn) -> RecommendResult:
    if not payload.user_query.strip():
        raise HTTPException(status_code=400, detail="user_query 不能为空")

    state_in = {
        "user_query": payload.user_query.strip(),
        "top_n": payload.top_n,
    }
    if payload.city_code_override:
        state_in["city_code_override"] = payload.city_code_override

    try:
        state_out = RECOMMEND_GRAPH.invoke(state_in)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Graph 执行失败：query=%s", payload.user_query)
        raise HTTPException(status_code=500, detail=f"Graph 执行失败：{exc!r}") from exc

    result_dict = state_out.get("result")
    if not result_dict:
        raise HTTPException(status_code=500, detail="Graph 返回缺 result 字段")
    return RecommendResult.model_validate(result_dict)


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
