# app/core/events.py
"""
应用生命周期事件处理

管理应用启动和关闭时的初始化和清理工作
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    启动时:
    - 初始化日志
    - 连接数据库
    - 连接 Redis
    - 初始化其他服务

    关闭时:
    - 关闭数据库连接
    - 关闭 Redis 连接
    - 清理资源
    """
    # ==================== 启动阶段 ====================
    logger.info(
        f"starting {settings.APP_NAME}   {settings.APP_VERSION}",
        extra={
            "environment": settings.APP_ENV,
            "debug": settings.DEBUG
        })
    # await init_database()

    # 初始化 Redis 连接池
    # await init_redis()

    # 初始化其他服务
    logger.info("Application startup complete")

    yield  # 应用运行期间

    # ==================== 关闭阶段 ====================
    logger.info("Shutting down application...")

    # 关闭数据库连接池
    # await close_database()

    # 关闭 Redis 连接池
    # await close_redis()

    logger.info("Application shutdown complete")
