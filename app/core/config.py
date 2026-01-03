# app/core/config.py
"""
应用配置管理模块

使用 Pydantic Settings 管理所有配置项，支持：
- 环境变量自动加载
- .env 文件加载
- 类型验证
- 默认值设置
"""
from functools import lru_cache
from typing import List, Optional, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== 应用基础配置 ====================
    APP_NAME: str = Field(default="nanochat", )
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "AI对话平台"
    APP_ENV: str = Field(default="development", description="运行环境: development, production")
    DEBUG: bool = Field(default=True, description="调试模式")

    # ==================== API 配置 ====================
    API_V1_PREFIX: str = Field(default="/api/v1", description="接口前缀")
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"

    # ==================== 安全配置 ====================
    SECRET_KEY: str = Field(description="应用密钥，用于 JWT 签名等")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access Token 过期时间（分钟）")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh Token 过期时间（天）")

    # ==================== CORS 配置 ====================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"],
        description="允许的跨域来源"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ==================== 数据库配置 ====================
    DATABASE_URL: str = Field(description="数据库连接 URL")
    DATABASE_POOL_SIZE: int = Field(default=20, description="连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="连接池溢出大小")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="连接回收时间（秒）")
    DATABASE_ECHO: bool = Field(default=False, description="是否打印 SQL 语句")

    # ==================== Redis 配置 ====================
    REDIS_URL: str = Field(description="Redis连接 URL")
    REDIS_MAX_CONNECTIONS: int = Field(default=10, description="Redis 最大连接数")

    # ==================== RabbitMQ 配置 ====================
    RABBITMQ_URL: str = Field(description="RabbitMQ 连接 URL")

    # ==================== MinIO 配置 ====================
    MINIO_ENDPOINT: str = Field(default="localhost:9000", description="MinIO 端点")
    MINIO_ACCESS_KEY: str = Field(description="MinIO Access Key")
    MINIO_SECRET_KEY: str = Field(description="MinIO Secret Key")
    MINIO_BUCKET: str = Field(default="nanochat", description="默认 Bucket")
    MINIO_SECURE: bool = Field(default=False, description="是否使用 HTTPS")

    # ==================== LLM 配置 ====================
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_API_BASE: str = Field(description="OpenAI API Base URL")
    DEFAULT_LLM_MODEL: str = Field(default="gpt-3.5-turbo", description="默认 LLM 模型")

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(default="json", description="日志格式: json, text")

    # ==================== 文件上传配置 ====================
    MAX_UPLOAD_SIZE: int = Field(default=50 * 1024 * 1024, description="最大上传文件大小（字节）")
    ALLOWED_UPLOAD_TYPES: List[str] = Field(
        default=["pdf", "docx", "doc", "txt", "md", "html", "csv"],
        description="允许的上传文件类型"
    )

    # ==================== 验证器 ====================
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """解析 CORS 来源配置"""
        if isinstance(v, str):
            # 支持逗号分隔的字符串
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL 不能为空")
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.APP_ENV == "production"

    @property
    def fastapi_kwargs(self) -> dict:
        """FastAPI 初始化参数"""
        kwargs = {
            "title": self.APP_NAME,
            "version": self.APP_VERSION,
            "description": self.APP_DESCRIPTION,
            "debug": self.DEBUG,
        }

        # 生产环境禁用文档
        if self.is_production:
            kwargs.update({
                "docs_url": None,
                "redoc_url": None,
                "openapi_url": None,
            })
        else:
            kwargs.update({
                "docs_url": self.DOCS_URL,
                "redoc_url": self.REDOC_URL,
                "openapi_url": self.OPENAPI_URL,
            })

        return kwargs


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    使用 lru_cache 确保配置只加载一次
    """
    return Settings()

# 导出配置实例
settings = get_settings()
