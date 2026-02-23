# app/core/jwt.py
"""
JWT Token 管理模块

提供：
- Access Token 生成与验证
- Refresh Token 生成与验证
- Token 载荷定义
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from pydantic import BaseModel

from app.core import settings


class TokenType:
    """Token 类型常量"""

    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    """Token 载荷"""

    sub: str  # 用户 ID
    tenant_id: str  # 租户 ID
    email: str  # 用户邮箱
    type: str  # Token 类型
    jti: str  # Token 唯一标识
    iat: datetime  # 签发时间
    exp: datetime  # 过期时间


class TokenPair(BaseModel):
    """Token 对"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access Token 过期秒数


def create_access_token(
        user_id: str,
        tenant_id: str,
        email: str,
        expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """
    创建 Access Token

    Args:
        user_id: 用户 ID
        tenant_id: 租户 ID
        email: 用户邮箱
        expires_delta: 过期时间增量

    Returns:
        tuple: (token, jti, expire_time)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.utcnow()
    expire = now + expires_delta
    jti = str(uuid.uuid4())

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "type": TokenType.ACCESS,
        "jti": jti,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def create_refresh_token(
        user_id: str,
        tenant_id: str,
        expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """
    创建 Refresh Token

    Args:
        user_id: 用户 ID
        tenant_id: 租户 ID
        expires_delta: 过期时间增量

    Returns:
        tuple: (token, jti, expire_time)
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.utcnow()
    expire = now + expires_delta
    jti = str(uuid.uuid4())

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": TokenType.REFRESH,
        "jti": jti,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def create_token_pair(
        user_id: str,
        tenant_id: str,
        email: str,
) -> tuple[TokenPair, str, str]:
    """
    创建 Token 对

    Args:
        user_id: 用户 ID
        tenant_id: 租户 ID
        email: 用户邮箱

    Returns:
        tuple: (TokenPair, access_jti, refresh_jti)
    """
    access_token, access_jti, _ = create_access_token(user_id, tenant_id, email)
    refresh_token, refresh_jti, _ = create_refresh_token(user_id, tenant_id)

    token_pair = TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return token_pair, access_jti, refresh_jti


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    解码 Token

    Args:
        token: JWT Token

    Returns:
        Optional[TokenPayload]: Token 载荷或 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


def verify_token(token: str, expected_type: str) -> Optional[TokenPayload]:
    """
    验证 Token

    Args:
        token: JWT Token
        expected_type: 期望的 Token 类型

    Returns:
        Optional[TokenPayload]: Token 载荷或 None
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # 验证 Token 类型
    if payload.type != expected_type:
        return None

    # 验证是否过期
    if payload.exp < datetime.utcnow():
        return None

    return payload


def get_token_remaining_time(token: str) -> int:
    """
    获取 Token 剩余有效时间（秒）

    Args:
        token: JWT Token

    Returns:
        int: 剩余秒数，如果已过期返回 0
    """
    payload = decode_token(token)
    if payload is None:
        return 0

    remaining = (payload.exp - datetime.utcnow()).total_seconds()
    return max(0, int(remaining))