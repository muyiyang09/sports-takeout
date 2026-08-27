"""配置中心：基于 pydantic-settings 的强类型配置。
通过 .env 文件或环境变量加载，避免把密钥硬编码进代码。
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # —— LLM（通过 LiteLLM 路由，支持 DeepSeek / 通义 / OpenAI 等）——
    llm_model: str = Field(
        default="deepseek/deepseek-chat",
        description="LiteLLM 模型标识，如 deepseek/deepseek-chat / qwen/qwen-plus / openai/gpt-4o-mini",
    )
    llm_api_key: str = Field(default="", description="对应供应商的 API Key")
    llm_base_url: Optional[str] = Field(
        default=None,
        description="自定义兼容端点。留空时 LiteLLM 会根据模型名选择官方端点。",
    )
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    llm_timeout: int = Field(default=60, description="单次 LLM 请求超时（秒）")
    llm_max_retries: int = Field(default=2, description="LiteLLM 内部重试次数")

    # —— MySQL（只读，查 coach/course 等现有表）——
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "sports_takeout"
    # —— MySQL 连接池（#05 上线加固：显式配池，避免默认 5 连接被打满）——
    mysql_pool_size: int = Field(default=20, description="连接池常驻连接数")
    mysql_max_overflow: int = Field(default=10, description="池满后可临时超出的连接数")
    mysql_pool_timeout: int = Field(default=30, description="获取连接超时（秒）")

    # —— Redis（推荐结果缓存，可选）——
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 1
    redis_password: Optional[str] = None

    # —— 混合检索（#04 RAG 升级）——
    # 设计：混合检索是「加强」不是「替代」——BM25 便宜且离线可跑，默认开；
    # 向量/重排依赖 bge-m3 / FlagEmbedding 重模型，国内下载困难，默认关、留开关待接入。
    hybrid_retrieval_enabled: bool = Field(
        default=True,
        description="是否启用混合检索（BM25+RRF 升级语义匹配维度；关闭则完全退回 #03 子串匹配）",
    )
    reranker_enabled: bool = Field(
        default=False,
        description="是否启用 Cross-Encoder 重排（依赖 bge-reranker 重模型，默认关）",
    )
    bm25_top_k: int = Field(default=50, description="BM25 召回条数")
    rrf_k: int = Field(default=60, description="RRF 平滑常数（业界经验值）")
    rrf_top_k: int = Field(default=30, description="RRF 融合后取前 N 进入重排/打分")

    # —— 向量召回 / 重排模型（预留：重依赖未装时自动降级为 BM25 单路）——
    embedding_model: str = Field(default="BAAI/bge-m3", description="Embedding 模型名（HuggingFace）")
    embedding_device: str = Field(default="cpu", description="cpu / cuda / mps")
    embedding_use_fp16: bool = Field(default=True)
    # 向量库后端选择：chroma（开发）/ pgvector（生产首选）/ chroma_http（过渡）
    vector_db_backend: str = Field(
        default="chroma", pattern=r"^(chroma|chroma_http|pgvector)$",
        description="向量库后端：chroma（本地文件，开发）/ chroma_http（Docker 独立部署，过渡）/ pgvector（PostgreSQL 扩展，生产首选）",
    )
    vector_db_path: str = Field(default="./data/chroma", description="Chroma 本地持久化目录（仅 chroma 模式）")
    vector_skip_initial_upsert: bool = Field(
        default=False, description="启动时是否跳过 upsert（已建索引时 True 加速启动）"
    )
    # pgvector 连接配置（仅 vector_db_backend=pgvector 时用）
    pgvector_host: str = Field(default="127.0.0.1", description="PostgreSQL 主机")
    pgvector_port: int = Field(default=5432, description="PostgreSQL 端口")
    pgvector_user: str = Field(default="postgres", description="PostgreSQL 用户名")
    pgvector_password: str = Field(default="", description="PostgreSQL 密码")
    pgvector_database: str = Field(default="sports_takeout", description="PostgreSQL 数据库名")
    pgvector_table: str = Field(default="ai_vector_coach", description="pgvector 向量表名")
    pgvector_dim: int = Field(default=1024, description="向量维度（bge-m3=1024）")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", description="Reranker 模型名")
    reranker_device: str = Field(default="cpu", description="cpu / cuda / mps")
    reranker_use_fp16: bool = Field(default=True)

    # —— 商业化加固（#05）：限流 / Token 预算 / 熔断 / 缓存 ——
    # 设计：这些管控都依赖 Redis。Redis 不可用时一律「fail-open」——放过流量而非全拦，
    # 避免「保护组件本身故障」把整个服务打挂（见各中间件的降级注释）。
    rl_global_per_min: int = Field(default=100, description="全局每分钟限流")
    rl_ip_per_min: int = Field(default=30, description="单 IP 每分钟限流")
    rl_user_per_min: int = Field(default=10, description="单用户每分钟限流")
    token_per_request_limit: int = Field(default=10000, description="单次请求输入 token 上限")
    token_user_daily_limit: int = Field(default=100000, description="单用户单日 token 上限")
    token_global_daily_limit: int = Field(default=1000000, description="全局单日 token 上限")
    cb_fail_threshold: int = Field(default=5, description="LLM 连续失败 N 次触发熔断")
    cb_reset_timeout: int = Field(default=60, description="熔断开路后多久进入半开试探（秒）")
    cache_enabled: bool = Field(default=True, description="是否启用推荐结果缓存（相同 query 24h 复用）")
    cache_ttl: int = Field(default=86400, description="缓存 TTL（秒），默认 24h")

    # —— MCP 工具层（#07，默认关：单 Agent 单进程直接调用够用）——
    mcp_enabled: bool = Field(default=False, description="是否启用 MCP 工具层（跨语言/外部 LLM）")
    mcp_server_port: int = Field(default=18001, description="MCP Server 端口")
    mcp_server_url: str = Field(default="http://localhost:18001/mcp", description="MCP Server URL")

    # —— 多 Agent（#08）——
    review_summary_enabled: bool = Field(default=True, description="是否启用评价摘要 Agent")
    cert_review_enabled: bool = Field(default=True, description="是否启用证书审核 Agent")
    supervisor_enabled: bool = Field(default=False, description="统一入口 Supervisor（默认关，直接调子 Agent）")
    hitl_enabled: bool = Field(default=False, description="是否启用 HITL 人工介入（证书审核最终确认，默认关）")

    # —— Checkpointer（上线加固：崩溃恢复 + 多副本共享状态 + DB 灾备）——
    checkpointer_backend: str = Field(
        default="memory", pattern=r"^(memory|redis)$",
        description="Checkpointer 后端：memory（开发）/ redis（生产，多副本共享 + TTL）",
    )
    checkpoint_ttl_minutes: int = Field(default=60, description="Checkpoint TTL（分钟），教练推荐/摘要 1h 足够")
    checkpoint_db_fallback: bool = Field(
        default=True,
        description="是否启用 DB 灾备层（Redis miss 时从 DB 读 state + 回填 Redis，防雪崩/穿透/击穿）",
    )

    # —— HTTP 服务 ——
    service_host: str = "0.0.0.0"
    service_port: int = 18000
    service_env: str = Field(default="dev", pattern=r"^(dev|test|prod)$")

    @property
    def mysql_dsn(self) -> str:
        pwd = f":{self.mysql_password}" if self.mysql_password else ""
        return (
            f"mysql+pymysql://{self.mysql_user}{pwd}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}"
                f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
