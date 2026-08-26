"""教练推荐 Graph（LangGraph + LiteLLM + Pydantic）。

拓扑（3 节点串行 + START → END）：

  ┌───────────────┐   ┌───────────────────┐   ┌────────────────────────┐
  │ Node 1        │   │ Node 2            │   │ Node 3                 │
  │ 意图抽取 LLM  │──▶│ 结构化检索 + 打分 │──▶│ 推荐理由生成 LLM       │
  │ 结构化 JSON   │   │ 纯 SQL/规则，无LLM│   │ 自然语言 2~3 句        │
  └───────────────┘   └───────────────────┘   └────────────────────────┘
          ▲                       ▲                         │
          │                       │                         ▼
   用户自然语言            MySQL coach 表              RecommendResult

设计要点：
  • Node 2 不调用 LLM，用「结构化条件 + 规则打分 + SQL」——
    这比让 LLM 在成百上千教练里选 Top3 更准、也便宜 10 倍。
  • 只有 Node 1（自然语言 → 条件）、Node 3（生成人话理由）才用 LLM。
  • 全程 Pydantic 强类型 + normalize 结构适配层，拒绝 LLM 漂移引发硬失败。
"""
from __future__ import annotations

import logging
from typing import Any, Optional, TypedDict

from app.clients.db import fetch_all
from app.clients.llm import chat, chat_structured, is_mock_mode, mock_structured
from app.graphs.base import END, START, StateGraph
from app.schemas.coach_recommend import (
    CoachCandidate,
    IntentExtraction,
    RecommendResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# State：Graph 全局状态，每个节点读 state + 写回 dict（LangGraph 自动 merge）
# =============================================================================
class RecommendState(TypedDict, total=False):
    # 入参
    user_query: str                 # 用户原始自然语言
    city_code_override: str         # 小程序端已知用户城市时可以强制覆盖，避免 LLM 抽错
    top_n: int                      # 返回多少个教练，默认 3
    # 节点中间产物
    intent: dict[str, Any]          # Node 1 输出：IntentExtraction.model_dump()
    candidates: list[dict[str, Any]]# Node 2 输出：list[CoachCandidate.model_dump()]
    matched_course: dict[str, Any]  # Node 2 输出：匹配课程 {name, price, category}
    over_budget: bool               # Node 2 输出：匹配课程是否超预算
    # 最终输出
    result: dict[str, Any]          # RecommendResult.model_dump()
    used_mock: bool                 # 是否走了 mock 路径


# =============================================================================
# Node 1：用户自然语言 → 结构化筛选条件（IntentExtraction）
# =============================================================================
SYSTEM_NODE1 = """你是一个「上门私教教练推荐」的结构化意图抽取器。
只根据用户一句话，输出 JSON：
  - city_name/district：用户提到的服务城市 / 商圈；
  - specialization / specialization_tags：用户的健身目标（减脂/增肌/拉伸/产后恢复等）；
  - level/min_rating：如果用户提到"金牌教练""至少 4.5 分"等则抽取；
  - max_price：用户预算；
  - time_slot：用户提到的时段；
  - male_only：用户明确要求男教练 True、女教练 False、没提则 null；
  - user_goal：用户一句话目标（用于推荐理由个性化）。

不要编造用户没提到的条件，没提一律 null / []。
"""


def extract_intent(state: RecommendState) -> dict[str, Any]:
    """Node 1。返回 {'intent': IntentExtraction dict, 'used_mock': bool}"""
    user_query = state.get("user_query") or ""
    city_override = state.get("city_code_override")
    used_mock = False

    if is_mock_mode():
        logger.info("[Recommend Node1] Mock 模式：用规则抽取 fallback")
        intent = _mock_extract_intent(user_query)
        used_mock = True
    else:
        intent_obj = chat_structured(
            messages=[
                {"role": "system", "content": SYSTEM_NODE1},
                {"role": "user", "content": user_query},
            ],
            output_schema=IntentExtraction,
        )
        intent = intent_obj.model_dump()

    # 小程序端如果已经知道城市（通过定位/用户配置），直接覆盖 LLM 结果，避免"我在朝阳"→ 城市被抽成别的
    if city_override:
        intent["city_name"] = city_override

    # 保证 specialization_tags 始终是 list
    intent.setdefault("specialization_tags", [])
    return {"intent": intent, "used_mock": used_mock}


# ---------------------------------------------------------------------------
# Mock 用的超简单关键词正则（离线 demo 专用）
# ---------------------------------------------------------------------------
def _mock_extract_intent(query: str) -> dict[str, Any]:
    q = (query or "").lower()
    d: dict[str, Any] = {
        "city_name": None,
        "district": None,
        "specialization": None,
        "specialization_tags": [],
        "level": None,
        "min_rating": None,
        "max_price": None,
        "time_slot": None,
        "male_only": None,
        "user_goal": query or None,
    }
    # 只做几个高命中关键词，作为离线演示
    if any(k in q for k in ("减脂", "减肥", "瘦", "燃脂", "塑形")):
        d["specialization"] = "减脂塑形"
        d["specialization_tags"].append("减脂")
    if any(k in q for k in ("增肌", "力量", "壮", "哑铃")):
        d["specialization"] = d["specialization"] or "增肌训练"
        d["specialization_tags"].append("增肌")
    if any(k in q for k in ("产后", "孕产", "修复")):
        d["specialization"] = "产后恢复"
        d["specialization_tags"].append("产后恢复")
    if any(k in q for k in ("拉伸", "放松", "康复", "疼痛")):
        d["specialization"] = d["specialization"] or "拉伸放松"
        d["specialization_tags"].append("拉伸")

    if "北京" in q:
        d["city_name"] = "北京市"
    if "望京" in q:
        d["district"] = "望京"
        d["city_name"] = d["city_name"] or "北京市"
    if "朝阳" in q:
        d["district"] = d["district"] or "朝阳区"
        d["city_name"] = d["city_name"] or "北京市"

    if "金牌" in q:
        d["level"] = 4
    if "高级" in q and d["level"] is None:
        d["level"] = 3

    # 价格：找数字 + 元/块/以内/以下
    import re

    m = re.search(r"(\d+)\s*(?:元|块|以内|以下|/次|每次|一次)", q)
    if m:
        d["max_price"] = float(m.group(1))

    if any(k in q for k in ("周末", "周六", "周日")):
        d["time_slot"] = "周末"
    elif any(k in q for k in ("晚上", "下班后")):
        d["time_slot"] = "工作日晚上"
    return d


# =============================================================================
# Node 2：按结构化条件查教练库 + 规则打分（无 LLM，纯 SQL + 加权）
# =============================================================================
# 打分权重（价格维度已移除，见项目决策：价格在教练间无价差，原 25% 摊给评分/匹配）：
#   评分 40% / 语义匹配 35% / 等级 10% / 距离(半径) 10% / 档期 5%
_WEIGHTS: dict[str, float] = {
    "rating": 0.40,
    "match": 0.35,
    "level": 0.10,
    "distance": 0.10,
    "schedule": 0.05,
}

# 用户目标关键词 → 可匹配教练 bio 的同义/扩展词（用于子串匹配）
_SPEC_SYNONYMS: dict[str, list[str]] = {
    "减脂": ["减脂", "减肥", "瘦身", "燃脂", "体脂", "塑形"],
    "增肌": ["增肌", "增重", "力量", "体能", "健美"],
    "产后": ["产后", "孕产", "修复", "恢复"],
    "拉伸": ["拉伸", "放松", "筋膜", "松解"],
    "康复": ["康复", "运动康复", "理疗", "疼痛"],
    "体态": ["体态", "矫正", "姿态"],
    "青少年": ["青少年", "儿童", "少儿"],
}

# 本地"假教练库 / 假课程目录"：MySQL 不可用时的离线兜底，与 SQL 种子保持一致。
_MOCK_COACHES: list[dict[str, Any]] = [
    {"coach_id": 1, "name": "李教练", "sex": "1", "level": 4, "rating": 4.9,
     "service_radius_km": 8.0, "city_name": "北京市", "bio": "国职认证，专注减脂塑形 8 年"},
    {"coach_id": 2, "name": "王教练", "sex": "2", "level": 3, "rating": 4.8,
     "service_radius_km": 5.0, "city_name": "北京市", "bio": "擅长增肌与体能训练"},
    {"coach_id": 3, "name": "张教练", "sex": "1", "level": 2, "rating": 4.7,
     "service_radius_km": 10.0, "city_name": "北京市", "bio": "运动康复方向，产后恢复经验丰富"},
]

_MOCK_COURSES: list[dict[str, Any]] = [
    {"category": "减脂塑形", "name": "上门减脂私教课", "price": 199.0},
    {"category": "增肌训练", "name": "上门增肌训练课", "price": 229.0},
    {"category": "拉伸放松", "name": "拉伸放松课", "price": 129.0},
]


# ---------------------------------------------------------------------------
# 数据获取：MySQL 只读（失败回退 mock）
# ---------------------------------------------------------------------------
def _normalize_coach(c: dict[str, Any]) -> dict[str, Any]:
    """把 DB 行 / mock 行统一成下游用到的 coach 结构。"""
    return {
        "coach_id": int(c.get("coach_id", c.get("id"))),
        "name": c.get("name", ""),
        "sex": c.get("sex"),
        "level": int(c.get("level") or 1),
        "rating": float(c.get("rating") or 0),
        "service_radius_km": float(c.get("service_radius_km") or 0),
        "city_name": c.get("city_name") or "",
        "bio": c.get("bio") or "",
    }


def _fetch_coaches(city_name: Optional[str]) -> list[dict[str, Any]]:
    """取「已审核正常(status=1)」教练；MySQL 失败/无结果回退 mock。"""
    try:
        sql = (
            "SELECT id, name, sex, level, rating, service_radius_km, city_code, city_name, bio "
            "FROM coach WHERE status = 1"
        )
        params: dict[str, Any] = {}
        if city_name:
            sql += " AND city_name = :city_name"
            params["city_name"] = city_name
        rows = fetch_all(sql, params)
        if rows:
            return [_normalize_coach(r) for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.warning("MySQL 教练查询失败，回退 mock：%s", exc)
    return [_normalize_coach(c) for c in _MOCK_COACHES]


def _fetch_courses() -> list[dict[str, Any]]:
    """课程目录（course JOIN category，仅起售/课程分类）。失败回退 mock。"""
    try:
        sql = (
            "SELECT c.name AS name, c.price AS price, cat.name AS category "
            "FROM course c LEFT JOIN category cat ON c.category_id = cat.id "
            "WHERE c.status = 1 AND cat.type = 1"
        )
        rows = fetch_all(sql)
        if rows:
            return [
                {"name": r.get("name"), "price": float(r.get("price") or 0),
                 "category": r.get("category") or ""}
                for r in rows
            ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("MySQL 课程目录查询失败，回退 mock：%s", exc)
    return list(_MOCK_COURSES)


def _fetch_available_slots(coach_ids: list[int]) -> Optional[dict[int, list[str]]]:
    """每个教练「未来可约」时段 {coach_id: [time_slot,...]}；MySQL 失败返回 None。"""
    if not coach_ids:
        return {}
    try:
        placeholders = ", ".join(str(int(i)) for i in coach_ids)
        sql = (
            "SELECT coach_id, time_slot FROM coach_schedule "
            f"WHERE status = 1 AND schedule_date >= CURDATE() AND coach_id IN ({placeholders})"
        )
        rows = fetch_all(sql)
        slots: dict[int, list[str]] = {}
        for r in rows:
            slots.setdefault(int(r["coach_id"]), []).append(r["time_slot"])
        return slots
    except Exception as exc:  # noqa: BLE001
        logger.warning("MySQL 排期查询失败，档期按默认处理：%s", exc)
        return None


# ---------------------------------------------------------------------------
# 打分辅助：语义匹配 / 课程匹配 / 预算 / 档期 / 距离
# ---------------------------------------------------------------------------
def _expand_keywords(specialization: Optional[str], tags: list[str]) -> list[str]:
    """把用户的 specialization + tags 展开成可用于 bio 子串匹配的关键词集合。"""
    kws: list[str] = []
    for t in list(tags or []) + [specialization or ""]:
        t = (t or "").strip()
        if not t:
            continue
        kws.append(t)
        for canonical, synonyms in _SPEC_SYNONYMS.items():
            if canonical in t or any(s in t for s in synonyms):
                kws.extend(synonyms)
    seen: set[str] = set()
    out: list[str] = []
    for k in kws:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _match_bio_score(bio: str, keywords: list[str]) -> int:
    """0~100：用户目标关键词在教练 bio 里的命中程度。"""
    if not keywords:
        return 70  # 用户没目标，给中位分
    bio_l = (bio or "").lower()
    hits = [k for k in keywords if k.lower() in bio_l]
    if not hits:
        return 40  # 有关键词但都不命中：给低分，不直接剔除
    return min(100, 50 + 30 + min(20, (len(hits) - 1) * 10))


def _match_course(specialization: Optional[str], tags: list[str],
                  courses: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """从课程目录挑一门最匹配用户目标的课（用于参考价 + 预算过滤）。"""
    if not courses:
        return None
    keywords = _expand_keywords(specialization, tags)
    best, best_hits = None, -1
    for c in courses:
        blob = f"{c.get('category', '')} {c.get('name', '')}".lower()
        hits = sum(1 for k in keywords if k.lower() in blob)
        if hits > best_hits:
            best, best_hits = c, hits
    if best_hits <= 0:
        # 无关键词命中时，取最便宜的一门（更保守、更贴合预算）
        return min(courses, key=lambda c: float(c.get("price") or 10**9))
    return best


def _apply_budget(matched: Optional[dict[str, Any]], max_price: Optional[float],
                  courses: list[dict[str, Any]]) -> tuple[Optional[dict[str, Any]], bool]:
    """预算过滤：优先挑「同类且预算内」的课；没有则保留原课并标记超预算。"""
    if matched is None:
        return None, False
    if max_price is None or float(matched.get("price") or 0) <= float(max_price):
        return matched, False
    cheaper = [
        c for c in courses
        if c.get("category") == matched.get("category")
        and float(c.get("price") or 0) <= float(max_price)
    ]
    if cheaper:
        return min(cheaper, key=lambda c: float(c["price"])), False
    return matched, True


def _time_bucket(time_slot: Optional[str]) -> Optional[str]:
    """把用户时段粗分成 morning/afternoon/evening；无法判断返回 None。"""
    if not time_slot:
        return None
    s = str(time_slot)
    if any(k in s for k in ("上午", "早上", "凌晨", "早晨")):
        return "morning"
    if any(k in s for k in ("下午", "中午")):
        return "afternoon"
    if any(k in s for k in ("晚上", "夜", "下班后")):
        return "evening"
    return None


def _slot_bucket(slot: str) -> str:
    """把 coach_schedule.time_slot（如 '09:00-10:00'）按开始小时粗分桶。"""
    try:
        hour = int(str(slot).split(":")[0])
    except (ValueError, IndexError):
        return "any"
    if hour < 12:
        return "morning"
    if hour < 18:
        return "afternoon"
    return "evening"


def _schedule_ratio(slots: list[str], bucket: Optional[str]) -> float:
    """档期匹配比（0~1）。"""
    if bucket is None:
        return 1.0 if slots else 0.5  # 没指定时段：有档期给满，无档期给 0.5 兜底
    matched = [s for s in slots if _slot_bucket(s) == bucket]
    if matched:
        return 1.0
    return 0.6 if slots else 0.0  # 该时段没空但有其他档期给 0.6；完全无档期给 0


def _distance_score(service_radius_km: float) -> int:
    """无用户坐标，用服务半径近似「可达性」：半径越大越可能覆盖到用户。"""
    return min(100, int(float(service_radius_km or 0) / 15.0 * 100))


def retrieve_and_rank(state: RecommendState) -> dict[str, Any]:
    """Node 2：真读 MySQL（失败回退 mock）+ 5 维加权打分，返回 candidates + 匹配课程。"""
    intent = state.get("intent") or {}
    top_n = int(state.get("top_n") or 3)
    max_price = intent.get("max_price")
    min_level = intent.get("level")
    min_rating = intent.get("min_rating")
    city_name = intent.get("city_name")
    target_spec = intent.get("specialization")
    target_tags: list[str] = intent.get("specialization_tags") or []
    time_slot = intent.get("time_slot")
    male_only = intent.get("male_only")

    # ---- 1. 取数据（教练 / 课程目录 / 档期）----
    coaches = _fetch_coaches(city_name)
    courses = _fetch_courses()
    slots = _fetch_available_slots([c["coach_id"] for c in coaches])  # None=DB 不可用

    # ---- 2. 关键词 + 匹配课程 + 预算过滤 ----
    keywords = _expand_keywords(target_spec, target_tags)
    matched_course = _match_course(target_spec, target_tags, courses)
    matched_course, over_budget = _apply_budget(matched_course, max_price, courses)
    ref_price = float(matched_course["price"]) if matched_course else 0.0
    ref_course_name = matched_course.get("name") if matched_course else None
    spec_label = matched_course.get("category") if matched_course else target_spec

    # ---- 3. 硬过滤 ----
    filtered: list[dict[str, Any]] = []
    for c in coaches:
        if city_name and c.get("city_name") != city_name:
            continue
        if min_level is not None and int(c.get("level", 0)) < int(min_level):
            continue
        if min_rating is not None and float(c.get("rating", 0)) < float(min_rating):
            continue
        if male_only is True and c.get("sex") != "1":
            continue
        if male_only is False and c.get("sex") != "0":
            continue
        filtered.append(c)

    # 一个都没命中就降过滤条件（兜底：至少给 top_n 个参考）
    if not filtered:
        filtered = list(coaches)

    # ---- 4. 5 维打分 + 加权综合 ----
    bucket = _time_bucket(time_slot)
    candidates: list[CoachCandidate] = []
    for c in filtered:
        score_rating = int(float(c.get("rating") or 0) / 5.0 * 100)
        score_level = int(int(c.get("level") or 1) / 4.0 * 100)
        score_match = _match_bio_score(c.get("bio") or "", keywords)
        score_distance = _distance_score(c.get("service_radius_km") or 0)
        if slots is None:
            ratio = 1.0  # DB 不可用，档期一律按「有空」处理
        else:
            ratio = _schedule_ratio(slots.get(c["coach_id"], []), bucket)
        score_schedule = int(ratio * 100)

        total = (
            score_rating * _WEIGHTS["rating"]
            + score_match * _WEIGHTS["match"]
            + score_level * _WEIGHTS["level"]
            + score_distance * _WEIGHTS["distance"]
            + score_schedule * _WEIGHTS["schedule"]
        )

        candidates.append(
            CoachCandidate(
                coach_id=int(c["coach_id"]),
                name=c.get("name", ""),
                level=int(c.get("level") or 1),
                rating=float(c.get("rating") or 0),
                service_radius_km=float(c.get("service_radius_km") or 0),
                city_name=c.get("city_name") or "",
                bio=c.get("bio") or "",
                specialization=spec_label,
                course_name=ref_course_name,
                price=ref_price,
                distance_km_est=None,
                schedule_match_ratio=round(ratio, 2),
                score_rating=score_rating,
                score_level=score_level,
                score_match=score_match,
                score_distance=score_distance,
                score_schedule=score_schedule,
                score_total=round(total, 2),
            )
        )

    # ---- 5. 按综合分降序，取 Top N ----
    candidates.sort(key=lambda x: x.score_total, reverse=True)
    top = candidates[:top_n]
    return {
        "candidates": [c.model_dump() for c in top],
        "matched_course": matched_course,
        "over_budget": over_budget,
    }


# =============================================================================
# Node 3：根据用户目标 + Top 教练，生成 2~3 句推荐理由（LLM）
# =============================================================================
SYSTEM_NODE3 = """你是「体育外卖」平台的健身顾问。你的任务：
根据用户目标和系统筛选出的 Top 教练列表，写 2~3 句自然语言推荐理由。
要求：
  - 语气真诚、口语化，避免硬广；
  - 结合用户具体目标（如产后恢复 / 减脂备婚），别空泛说"很棒很专业"；
  - 至少点出 2 位教练的 1 个差异化卖点（如「李教练评分 4.9 专注减脂 8 年」vs「张教练做产后恢复更有经验」）；
  - 100 字以内。
输出纯文本即可，不要 JSON。
"""


def _mock_generate_reason(
    intent: dict[str, Any],
    candidates: list[dict[str, Any]],
    matched_course: Optional[dict[str, Any]] = None,
    over_budget: bool = False,
) -> str:
    goal = intent.get("user_goal") or "找合适的教练"
    names = "、".join([c.get("name", "?") for c in candidates[:2]]) or "推荐的几位教练"
    course_txt = ""
    if matched_course:
        course_txt = (
            f"匹配课程「{matched_course.get('name')}」¥{float(matched_course.get('price') or 0):.0f}"
            + ("，略超你的预算" if over_budget else "，在你预算内")
        )
    return (
        f"针对你的目标「{goal}」，推荐先约 {names} 试试。"
        f"{course_txt}。几位教练评分高、擅长领域匹配，体验风险低。"
    )


def generate_reason(state: RecommendState) -> dict[str, Any]:
    """Node 3：生成推荐理由 + 组装最终 RecommendResult。"""
    user_query = state.get("user_query") or ""
    intent = state.get("intent") or {}
    candidates_dicts: list[dict[str, Any]] = state.get("candidates") or []
    matched_course = state.get("matched_course")
    over_budget = bool(state.get("over_budget"))
    used_mock = bool(state.get("used_mock")) or is_mock_mode()

    # 先把 candidates 还原成 Pydantic（保证结构合法）
    candidates_objs: list[CoachCandidate] = [
        CoachCandidate.model_validate(c) for c in candidates_dicts
    ]

    if used_mock:
        reason = _mock_generate_reason(intent, candidates_dicts, matched_course, over_budget)
    else:
        top_coaches_brief = "\n".join(
            [
                f"- {c.name}（{['初','中','高','金'][c.level-1]}牌，评分{c.rating}，"
                f"擅长：{c.bio or c.specialization or '未填写'}，参考课 ¥{c.price:.0f}，综合分{c.score_total:.1f}）"
                for c in candidates_objs
            ]
        ) or "（无候选）"
        user = f"用户目标：{intent.get('user_goal') or user_query}"
        try:
            reason = chat(
                messages=[
                    {"role": "system", "content": SYSTEM_NODE3},
                    {"role": "user", "content": f"{user}\n\n候选教练：\n{top_coaches_brief}"},
                ]
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Node3 推荐理由 LLM 失败，回退 mock：%s", exc)
            reason = _mock_generate_reason(intent, candidates_dicts, matched_course, over_budget)
            used_mock = True

    # ---- 组装最终结果 ----
    result_obj = RecommendResult(
        user_query=user_query,
        intent=IntentExtraction.model_validate(intent),
        candidates=candidates_objs,
        coach_ids=[c.coach_id for c in candidates_objs],
        recommend_reason=reason,
        matched_course_name=(matched_course.get("name") if matched_course else None),
        matched_course_price=(float(matched_course["price"]) if matched_course else None),
        over_budget=over_budget,
        used_mock=used_mock,
    )
    return {"result": result_obj.model_dump(), "used_mock": used_mock}


# =============================================================================
# Graph 编译
# =============================================================================
_builder = StateGraph(RecommendState)
_builder.add_node("extract_intent", extract_intent)
_builder.add_node("retrieve_and_rank", retrieve_and_rank)
_builder.add_node("generate_reason", generate_reason)

_builder.add_edge(START, "extract_intent")
_builder.add_edge("extract_intent", "retrieve_and_rank")
_builder.add_edge("retrieve_and_rank", "generate_reason")
_builder.add_edge("generate_reason", END)

RECOMMEND_GRAPH = _builder.compile()
"""对外的推荐图。使用方式：

    from app.graphs.recommend_coach import RECOMMEND_GRAPH
    state_out = RECOMMEND_GRAPH.invoke({
        "user_query": "我家住望京，预算 200 以内，想产后恢复",
        "top_n": 3,
    })
    result = RecommendResult.model_validate(state_out["result"])
"""


__all__ = [
    "RecommendState",
    "RECOMMEND_GRAPH",
    "extract_intent",
    "retrieve_and_rank",
    "generate_reason",
]
