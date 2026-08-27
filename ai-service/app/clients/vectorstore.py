"""向量存储客户端（#04 向量路，三后端可切换）。

后端选择（通过 settings.vector_db_backend 配置）：
  - **chroma**（默认，开发）：Chroma PersistentClient，本地文件存储，零运维
  - **chroma_http**（过渡）：Chroma HttpClient，Docker 独立部署，多副本共享
  - **pgvector**（生产首选）：PostgreSQL + pgvector 扩展，HA + 主从复制 + 成熟运维

为什么 pgvector 是生产首选：
  - 多副本共享（PostgreSQL 原生网络访问，不像 PersistentClient 是本地文件）
  - HA（主从复制 + 自动 failover）
  - 事务一致性（向量数据和业务数据可同库，插入原子性）
  - HNSW 索引（pgvector 0.5+，ms 级查询）
  - 运维工具链成熟（pg_dump / Prometheus / Grafana）

设计要点：
  - 惰性初始化：首次访问才建连接 / 建表，不拖慢启动；
  - 失败即降级：任何异常都返回 [] / 0，不抛给主链路（BM25 单路兜底）；
  - 统一接口：三种后端对外暴露相同的 upsert / search 语义（适配器模式）。
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.clients.embedding import embed, embed_one
from app.config import settings

logger = logging.getLogger(__name__)

# 全局后端实例 + 可用性标记
_backend: Any = None
_available: bool | None = None  # None=未探测；探测后缓存


# =============================================================================
# 后端适配器（鸭子类型：都实现 upsert / query 两个方法）
# =============================================================================

class _ChromaBackend:
    """Chroma PersistentClient（本地文件，开发用）。"""

    def __init__(self):
        import chromadb  # type: ignore
        client = chromadb.PersistentClient(path=settings.vector_db_path)
        self._store = client.get_or_create_collection(
            name="coach_bio",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("[VectorStore] Chroma PersistentClient 就绪，path=%s", settings.vector_db_path)

    def upsert(self, ids: list[str], embeddings: list, documents: list[str], metadatas: list[dict]):
        self._store.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, query_embeddings: list, n_results: int) -> dict:
        """返回 Chroma 风格结构：{ids, distances, metadatas}"""
        return self._store.query(query_embeddings=query_embeddings, n_results=n_results)


class _ChromaHttpBackend:
    """Chroma HttpClient（Docker 独立部署，过渡方案）。

    多副本可共享同一 Chroma 实例，但仍非 HA（单节点）。
    生产最终应迁到 pgvector。
    """

    def __init__(self):
        import chromadb  # type: ignore
        # host:port 从 vector_db_path 解析（格式 "host:port"），或用默认
        parts = settings.vector_db_path.split(":") if ":" in settings.vector_db_path else ["localhost", "8000"]
        host = parts[0] if parts else "localhost"
        port = int(parts[1]) if len(parts) > 1 else 8000
        client = chromadb.HttpClient(host=host, port=port)
        self._store = client.get_or_create_collection(
            name="coach_bio",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("[VectorStore] Chroma HttpClient 就绪，host=%s port=%d", host, port)

    def upsert(self, ids, embeddings, documents, metadatas):
        self._store.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, query_embeddings, n_results) -> dict:
        return self._store.query(query_embeddings=query_embeddings, n_results=n_results)


class _PgvectorBackend:
    """pgvector 后端（PostgreSQL + pgvector 扩展，生产首选）。

    用 psycopg2 同步驱动 + asyncio.to_thread 包装（与 db.py 的 MySQL 访问模式一致），
    不引入 asyncpg 新驱动，降低依赖复杂度。
    """

    def __init__(self):
        import psycopg2  # type: ignore
        # 构建连接字符串
        dsn = (
            f"host={settings.pgvector_host} port={settings.pgvector_port} "
            f"user={settings.pgvector_user} password={settings.pgvector_password} "
            f"dbname={settings.pgvector_database}"
        )
        self._conn_factory = lambda: psycopg2.connect(dsn)
        self._table = settings.pgvector_table
        self._dim = settings.pgvector_dim

        # 建表 + 建索引（幂等）
        self._ensure_schema()
        logger.info(
            "[VectorStore] pgvector 就绪，host=%s db=%s table=%s dim=%d",
            settings.pgvector_host, settings.pgvector_database, self._table, self._dim,
        )

    def _ensure_schema(self):
        """建表 + 扩展 + HNSW 索引（幂等）。"""
        with self._conn_factory() as conn, conn.cursor() as cur:
            # 1. 装 pgvector 扩展
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            # 2. 建表
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    id         TEXT PRIMARY KEY,
                    embedding  vector({self._dim}),
                    document   TEXT,
                    metadata   JSONB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 3. 建 HNSW 索引（cosine 距离）
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self._table}_embedding
                ON {self._table} USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
            conn.commit()

    def upsert(self, ids: list[str], embeddings: list, documents: list[str], metadatas: list[dict]):
        """批量 upsert（ON CONFLICT 更新）。"""
        # pgvector 的 vector 字面量格式：'[0.1,0.2,...]'
        rows = []
        for i, cid in enumerate(ids):
            vec_str = "[" + ",".join(str(float(x)) for x in embeddings[i]) + "]"
            rows.append((cid, vec_str, documents[i], json.dumps(metadatas[i], ensure_ascii=False)))

        with self._conn_factory() as conn, conn.cursor() as cur:
            # executemany 批量 upsert
            cur.executemany(
                f"""
                INSERT INTO {self._table} (id, embedding, document, metadata)
                VALUES (%s, %s::vector, %s, %s::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    document = EXCLUDED.document,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
                """,
                rows,
            )
            conn.commit()

    def query(self, query_embeddings: list, n_results: int) -> dict:
        """向量近邻查询，返回 Chroma 风格结构。

        用 <=> 操作符（cosine distance），返回格式与 Chroma 对齐：
        {ids: [[...]], distances: [[...]], metadatas: [[...]]}
        """
        # pgvector 查询：单条 query 向量
        vec_str = "[" + ",".join(str(float(x)) for x in query_embeddings[0]) + "]"
        with self._conn_factory() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, metadata, embedding <=> %s::vector AS distance
                FROM {self._table}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vec_str, vec_str, n_results),
            )
            rows = cur.fetchall()

        # 转成 Chroma 风格结构（外层是 batch 维度，这里只有 1 个 query）
        ids = [[r[0] for r in rows]]
        metadatas = [[json.loads(r[1]) if r[1] else {} for r in rows]]
        distances = [[float(r[2]) for r in rows]]
        return {"ids": ids, "metadatas": metadatas, "distances": distances}


# =============================================================================
# 工厂 + 可用性探测
# =============================================================================

def _check_available() -> bool:
    """探测后端依赖是否可用。结果缓存，缺失只告警一次。"""
    global _available
    if _available is None:
        backend = settings.vector_db_backend
        try:
            if backend == "pgvector":
                import psycopg2  # noqa: F401
            else:
                import chromadb  # noqa: F401
            _available = True
        except ImportError as exc:
            logger.warning(
                "[VectorStore] 后端 %s 依赖未安装，向量召回降级为 BM25 单路：%s",
                backend, exc,
            )
            _available = False
    return _available


def _get_backend():
    """惰性获取后端实例。依赖缺失 / 初始化失败时抛 RuntimeError（上层降级）。"""
    global _backend
    if _backend is None:
        backend = settings.vector_db_backend
        if backend == "pgvector":
            _backend = _PgvectorBackend()
        elif backend == "chroma_http":
            _backend = _ChromaHttpBackend()
        else:
            _backend = _ChromaBackend()
    return _backend


# =============================================================================
# 公共接口（upsert_coaches / search）—— 上层不感知后端差异
# =============================================================================

def upsert_coaches(coaches: list[dict[str, Any]]) -> int:
    """批量 upsert 教练向量（启动 / 教练更新时调用）。不可用时返回 0。"""
    if not coaches or not _check_available():
        return 0
    try:
        backend = _get_backend()
        texts = [
            f"{c.get('name', '')} {c.get('bio', '')} {c.get('city_name', '')}"
            for c in coaches
        ]
        vectors = embed(texts)
        if not vectors.size:
            return 0
        backend.upsert(
            ids=[f"coach_{c['coach_id']}" for c in coaches],
            embeddings=vectors.tolist(),
            documents=texts,
            metadatas=[{"coach_id": c["coach_id"]} for c in coaches],
        )
        logger.info("[VectorStore] upsert %d 教练向量（后端=%s）", len(coaches), settings.vector_db_backend)
        return len(coaches)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[VectorStore] upsert 失败，跳过：%s", exc)
        return 0


def search(query: str, top_k: int = 50) -> list[tuple[int, float]]:
    """向量语义召回。返回 [(coach_id, similarity)]。不可用时返回 []。"""
    if not (query or "").strip() or not _check_available():
        return []
    try:
        backend = _get_backend()
        query_vec = embed_one(query)
        if not query_vec.size:
            return []
        result = backend.query(query_embeddings=[query_vec.tolist()], n_results=top_k)
        ids = [int(m["coach_id"]) for m in result["metadatas"][0]]
        # cosine distance → similarity = 1 - dist
        sims = [float(1 - d) for d in result["distances"][0]]
        return list(zip(ids, sims))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[VectorStore] 召回失败，降级为空：%s", exc)
        return []


__all__ = ["search", "upsert_coaches"]
