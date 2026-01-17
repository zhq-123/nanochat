# app/api/v1/endpoints/health.py
"""
健康检查接口

提供系统健康状态检查，包括：
- 应用状态
- 数据库连接
- Redis 连接
- RabbitMQ 连接
- MinIO 连接
"""
import asyncio
import time
from sys import exception
from typing import Any

import aio_pika
import asyncpg
import redis.asyncio
from fastapi.params import Depends, Query
from fastapi.routing import APIRoute, APIRouter
from minio import Minio

from app.api.deps import get_settings_dep
from app.core.config import Settings
from datetime import datetime, timezone

router = APIRouter()


@router.get(
    "",
    summary="健康检查",
    description="检查应用和各个服务的健康状态", )
async def health_check(
        settings: Settings = Depends(get_settings_dep)
) -> dict[str, Any]:
    """
    健康检查接口

    返回:
    - status: 整体状态 (healthy/unhealthy)
    - checks: 各服务检查结果
    - version: 应用版本
    - timestamp: 检查时间
    """
    checks = {}

    # 并发检查所有服务
    check_tasks = [
        ("database", _check_database(settings)),
        ("redis", _check_redis(settings)),
        ("rabbitmq", _check_rabbitmq(settings)),
        ("minio", _check_minio(settings)),
    ]

    results = await asyncio.gather(
        *[check for _, check in check_tasks],
        return_exceptions=True,
    )

    for (name, _), result in zip(check_tasks, results):
        if isinstance(result, Exception):
            checks[name] = {
                "status": "unhealthy",
                "error": str(result),
            }
        else:
            checks[name] = result

    # 判断整体状态
    overall_status = "heathy" if all(
        check.get("status") == "healthy"
        for check in checks.values()
    ) else "unhealthy"

    return {
        "status": overall_status,
        "checks": checks,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/live",
    summary="存活检查",
    description="简单的存活检查",
)
async def liveness() -> dict[str, Any]:
    return {"status": "ok"}


async def _check_database(settings: Settings) -> dict[str, Any]:
    """检查数据库连接"""
    start_time = time.time()
    try:
        # 从 DATABASE_URL 解析连接参数:postgresql+asyncpg://user:pass@host:port/db
        # 在直接使用 asyncpg 库时，必须使用标准的 postgresql:// 格式。
        # SQLAlchemy 风格的 postgresql+asyncpg:// 格式会导致 URL 解析失败。
        url = settings.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://")

        conn = await asyncpg.connect(url, timeout=5)
        await conn.execute("SELECT 1")
        await conn.close()

        latency = (time.time() - start_time) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def _check_redis(settings):
    """检查 Redis 连接"""
    start_time = time.time()
    try:
        redis_client = redis.asyncio.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()

        latency = (time.time() - start_time) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def _check_rabbitmq(settings):
    """检查 RabbitMQ 连接"""
    start_time = time.time()
    try:
        connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL,
            timeout=5,
        )
        await connection.close()

        latency = (time.time() - start_time) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def _check_minio(settings):
    """检查 MinIO 连接"""
    start_time = time.time()
    try:
        client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        # 检查 bucket 是否存在
        client.bucket_exists(settings.MINIO_BUCKET)

        latency = (time.time() - start_time) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
