# app/core/redis.py
"""
Redis 客户端模块

提供：
- Redis 连接管理
- 常用操作封装
"""
import logging
from typing import Optional, Any

import redis
from redis.asyncio import Redis

from app.core import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    获取 Redis 客户端

    Returns:
        Redis: Redis 客户端实例
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.asyncio.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS
        )

    return _redis_client


async def close_redis() -> None:
    """关闭 Redis 连接"""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")


async def init_redis() -> None:
    """初始化 Redis 连接"""
    client = await get_redis()
    await client.ping()
    logger.info("Redis connection initialized")


class RedisClient:
    """
    Redis 客户端封装

    提供常用操作的便捷方法
    """

    def __init__(self, client: Redis):
        self.client = client

    async def get(self, key:str) -> Optional[str]:
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
    ) -> bool:
        """
        设置值

        Args:
            key: 键
            value: 值
            ex: 过期时间（秒）
            px: 过期时间（毫秒）
        """
        return await self.client.set(key, value, ex=ex, px=px)

    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        return await self.client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        return await self.client.ttl(key)

    async def incr(self, key: str) -> int:
        """自增"""
        return await self.client.incr(key)

    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        """设置值并指定过期时间"""
        return await self.client.setex(key, seconds, value)

    async def setnx(self, key: str, value: Any) -> bool:
        """仅当键不存在时设置"""
        return await self.client.setnx(key, value)