# app/api/deps.py
"""
API 依赖注入模块

提供常用的依赖注入函数：
- 数据库会话
- 当前用户
- 分页参数
- 等等
"""
from typing import Optional, AsyncGenerator, Annotated

from fastapi import Depends
from fastapi.params import Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import AuthenticationException, ErrorCode
from app.db import get_async_session

from app.core.config import Settings, get_settings
from app.models import User
from app.repositories import UserRepository
from app.services.token_service import TokenService, get_token_service
from app.utils.jwt import TokenPayload, verify_token, TokenType

security = HTTPBearer(auto_error=False)

def get_settings_dep() -> Settings:
    """获取配置依赖"""
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话依赖

    用于 FastAPI 路由中注入数据库会话

    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async for session in get_async_session():
        yield session


class PaginationParams:
    """分页参数"""

    def __init__(self,
                 page: int = Query(default=1, ge=1, description="页码"),
                 page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
                 ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


class SortsParams:
    """排序参数"""

    def __init__(self,
                 sort: Optional[str] =
                 Query(default="-created_at", description="排序字段，-前缀表示降序")
                 ):
        self.sort = sort
        if sort:
            self.desc = sort.startswith("-")
            self.field = sort.lstrip("-")
        else:
            self.desc = True
            self.field = "created_at"


async def get_token_payload(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> TokenPayload:
    """
    获取并验证 Access Token

    Returns:
        TokenPayload: Token 载荷

    Raises:
        AuthenticationException: Token 无效或过期
    """
    if credentials is None:
        raise AuthenticationException(
            code=ErrorCode.UNAUTHORIZED,
            message="未提供认证信息",
        )

    token = credentials.credentials

    # 验证 Token 格式和签名
    payload = verify_token(token, TokenType.ACCESS)
    if payload is None:
        raise AuthenticationException(
            code=ErrorCode.TOKEN_INVALID,
            message="无效的认证令牌",
        )

    # 检查 Token 是否在黑名单中
    if await token_service.is_blacklisted(token):
        raise AuthenticationException(
            code=ErrorCode.TOKEN_INVALID,
            message="认证令牌已失效",
        )

    return payload


async def get_current_user(
    payload: Annotated[TokenPayload, Depends(get_token_payload)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    获取当前登录用户

    Returns:
        User: 当前用户

    Raises:
        AuthenticationException: 用户不存在或已禁用
    """
    from uuid import UUID

    user_repo = UserRepository(db)
    user = await user_repo.get_with_tenant(UUID(payload.sub))

    if user is None:
        raise AuthenticationException(
            code=ErrorCode.USER_NOT_FOUND,
            message="用户不存在",
        )

    if not user.is_active:
        raise AuthenticationException(
            code=ErrorCode.ACCOUNT_DISABLED,
            message="账号已被禁用",
        )

    if not user.tenant.is_active:
        raise AuthenticationException(
            code=ErrorCode.TENANT_DISABLED,
            message="所属租户已被禁用",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    获取当前活跃用户（别名）

    用于需要验证用户活跃状态的场景
    """
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    获取当前超级管理员用户

    Returns:
        User: 当前超级管理员

    Raises:
        AuthenticationException: 非超级管理员
    """
    if not current_user.is_superuser:
        raise AuthenticationException(
            code=ErrorCode.PERMISSION_DENIED,
            message="需要超级管理员权限",
        )
    return current_user


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    """
    获取可选的当前用户

    用于接口同时支持登录和未登录访问的场景

    Returns:
        Optional[User]: 当前用户或 None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token, TokenType.ACCESS)
        if payload is None:
            return None

        if await token_service.is_blacklisted(token):
            return None

        from uuid import UUID
        user_repo = UserRepository(db)
        user = await user_repo.get_with_tenant(UUID(payload.sub))

        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        return None


# 类型别名，便于路由中使用
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
