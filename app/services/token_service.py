# app/services/token_service.py
"""
Token 服务

提供：
- Token 黑名单管理
- Token 有效性检查
"""
import logging


from app.core.redis import get_redis, RedisClient
from app.utils.jwt import decode_token, get_token_remaining_time

logger = logging.getLogger(__name__)

# Redis Key 前缀
TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
REFRESH_TOKEN_PREFIX = "token:refresh:"


class TokenService:
    """Token 服务类"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    async def add_to_blacklist(self, token: str) -> bool:
        """
        将 Token 加入黑名单

        Args:
            token: JWT Token

        Returns:
            bool: 是否成功
        """
        payload = decode_token(token)
        if payload is None:
            return False

        # 获取 Token 剩余有效时间
        remaining_time = get_token_remaining_time(token)
        if remaining_time <= 0:
            # Token 已过期，无需加入黑名单
            return True

        # 将 jti 加入黑名单，过期时间设为 Token 剩余有效期
        key = f"{TOKEN_BLACKLIST_PREFIX}{payload.jti}"
        await self.redis.setex(key, remaining_time, "1")

        logger.info(
            "Token added to blacklist",
            extra={
                "jti": payload.jti,
                "user_id": payload.sub,
                "remaining_seconds": remaining_time,
            },
        )

        return True

    async def is_blacklisted(self, token: str) -> bool:
        """
        检查 Token 是否在黑名单中

        Args:
            token: JWT Token

        Returns:
            bool: 是否在黑名单中
        """
        payload = decode_token(token)
        if payload is None:
            return True

        key = f"{TOKEN_BLACKLIST_PREFIX}{payload.jti}"
        exists = await self.redis.exists(key)
        return exists > 0

    async def store_refresh_token(
        self,
        user_id: str,
        jti: str,
        expire_seconds: int,
    ) -> bool:
        """
        存储 Refresh Token 信息

        用于：
        - 限制用户同时登录的设备数
        - 强制下线所有设备

        Args:
            user_id: 用户 ID
            jti: Token 唯一标识
            expire_seconds: 过期时间（秒）

        Returns:
            bool: 是否成功
        """
        key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{jti}"
        return await self.redis.setex(key, expire_seconds, "1")

    async def revoke_refresh_token(self, user_id: str, jti: str) -> bool:
        """
        撤销指定的 Refresh Token

        Args:
            user_id: 用户 ID
            jti: Token 唯一标识

        Returns:
            bool: 是否成功
        """
        key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{jti}"
        await self.redis.delete(key)
        return True

    async def revoke_all_refresh_tokens(self, user_id: str) -> int:
        """
        撤销用户所有的 Refresh Token

        用于：强制下线所有设备

        Args:
            user_id: 用户 ID

        Returns:
            int: 撤销的 Token 数量
        """
        pattern = f"{REFRESH_TOKEN_PREFIX}{user_id}:*"
        cursor = 0
        deleted_count = 0

        # 使用 SCAN 遍历所有匹配的 key
        while True:
            cursor, keys = await self.redis.client.scan(
                cursor, match=pattern, count=100
            )
            if keys:
                await self.redis.delete(*keys)
                deleted_count += len(keys)
            if cursor == 0:
                break

        logger.info(
            "All refresh tokens revoked",
            extra={"user_id": user_id, "count": deleted_count},
        )

        return deleted_count

    async def is_refresh_token_valid(self, user_id: str, jti: str) -> bool:
        """
        检查 Refresh Token 是否有效

        Args:
            user_id: 用户 ID
            jti: Token 唯一标识

        Returns:
            bool: 是否有效
        """
        key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{jti}"
        exists = await self.redis.exists(key)
        return exists > 0


async def get_token_service() -> TokenService:
    """获取 Token 服务实例"""
    redis_client = await get_redis()
    return TokenService(RedisClient(redis_client))