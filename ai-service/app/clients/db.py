"""MySQL 只读访问层（SQLAlchemy 2.0 Core + pymysql）。

AI 服务只读现有 sports_takeout 库（coach / course / category / coach_schedule），
连接参数来自 config.settings.mysql_dsn。故意用「只读 + 惰性 engine + 查询函数」，
不引入 ORM 模型，保持与 Java 后端解耦：后端改了表，AI 服务只需改 SQL 字符串。
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """惰性创建全局 engine（连接池）。用只读账号即可。"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.mysql_dsn,
            pool_pre_ping=True,   # 取连接前先 ping，避免拿到失效连接
            pool_recycle=3600,
            echo=False,
            future=True,
        )
    return _engine


def fetch_all(sql: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """执行只读查询，返回 list[dict]（每行一个 dict，key 为列名）。"""
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params or {})
        cols = list(rows.keys())
        return [dict(zip(cols, row)) for row in rows]


def is_db_available() -> bool:
    """探活：MySQL 是否可连。用于上层决定走真库还是 mock 兜底。"""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("MySQL 不可用：%s", exc)
        return False
