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

    # —— Redis（推荐结果缓存，可选）——
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 1
    redis_password: Optional[str] = None

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
