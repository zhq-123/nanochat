# app/api/v1/endpoints/auth.py
"""
认证接口

提供用户注册、登录等认证相关 API
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.requests import Request

from app.api.deps import DBSession, CurrentUser
from app.core import settings, AuthenticationException, ErrorCode
from app.schemas import RegisterResponse, RegisterRequest, Response, UserOut, LoginResponse, LoginRequest
from app.schemas.auth import TokenResponse, RefreshTokenResponse, RefreshTokenRequest, LogoutRequest
from app.services import UserService, TokenService, get_token_service

from app.utils import success_response
from app.utils.jwt import create_token_pair, verify_token, TokenType, decode_token

logger = logging.getLogger(__name__)
router = APIRouter()


def get_client_ip(request: Request) -> str:
    """获取客户端 IP"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


@router.post(
    "/register",
    summary="用户注册",
    description="新用户注册，同时创建租户和返回 Token",
    response_model=Response[RegisterResponse],
)
async def register(
    request: Request,
    data: RegisterRequest,
    db: DBSession,
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> Response:
    """
    用户注册

    创建新用户和对应的租户，返回登录 Token

    - **email**: 邮箱（唯一）
    - **username**: 用户名（2-50字符）
    - **password**: 密码（至少8字符，包含大小写字母和数字）
    - **full_name**: 全名（可选）
    - **tenant_name**: 租户名称（可选，默认使用"用户名的工作空间"）
    """
    service = UserService(db)
    user, tenant = await service.register(data)

    # 生成 Token
    token_pair, access_jti, refresh_jti = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=user.email,
    )

    # 存储 Refresh Token
    await token_service.store_refresh_token(
        user_id=str(user.id),
        jti=refresh_jti,
        expire_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    response_data = RegisterResponse(
        user=UserOut.model_validate(user),
        tenant_id=str(tenant.id),
        token=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
        ),
        message="注册成功",
    )

    return success_response(
        data=response_data.model_dump(),
        message="注册成功",
        request=request,
    )


@router.post(
    "/login",
    summary="用户登录",
    description="使用邮箱和密码登录，返回 Token",
    response_model=Response[LoginResponse],
)
async def login(
    request: Request,
    data: LoginRequest,
    db: DBSession,
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> Response:
    """
    用户登录

    使用邮箱和密码进行身份验证，返回 Token

    - **email**: 注册邮箱
    - **password**: 密码
    """
    client_ip = get_client_ip(request)

    service = UserService(db)
    user = await service.authenticate(data, ip_address=client_ip)

    # 生成 Token
    token_pair, access_jti, refresh_jti = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
    )

    # 存储 Refresh Token
    await token_service.store_refresh_token(
        user_id=str(user.id),
        jti=refresh_jti,
        expire_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    response_data = LoginResponse(
        user=UserOut.model_validate(user),
        token=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
        ),
    )

    return success_response(
        data=response_data.model_dump(),
        message="登录成功",
        request=request,
    )


@router.post(
    "/refresh",
    summary="刷新 Token",
    description="使用 Refresh Token 获取新的 Token 对",
    response_model=Response[RefreshTokenResponse],
)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: DBSession,
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> Response:
    """
    刷新 Token

    使用 Refresh Token 获取新的 Access Token 和 Refresh Token

    - **refresh_token**: 有效的 Refresh Token
    """
    # 验证 Refresh Token
    payload = verify_token(data.refresh_token, TokenType.REFRESH)
    if payload is None:
        raise AuthenticationException(
            code=ErrorCode.REFRESH_TOKEN_EXPIRED,
            message="Refresh Token 无效或已过期",
        )

    # 检查 Refresh Token 是否在 Redis 中有效
    is_valid = await token_service.is_refresh_token_valid(
        user_id=payload.sub,
        jti=payload.jti,
    )
    if not is_valid:
        raise AuthenticationException(
            code=ErrorCode.REFRESH_TOKEN_EXPIRED,
            message="Refresh Token 已被撤销",
        )

    # 获取用户信息
    from uuid import UUID
    from app.repositories.user_repository import UserRepository

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

    # 撤销旧的 Refresh Token
    await token_service.revoke_refresh_token(
        user_id=payload.sub,
        jti=payload.jti,
    )

    # 生成新的 Token 对
    token_pair, access_jti, refresh_jti = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
    )

    # 存储新的 Refresh Token
    await token_service.store_refresh_token(
        user_id=str(user.id),
        jti=refresh_jti,
        expire_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    response_data = RefreshTokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )

    logger.info(
        "Token refreshed",
        extra={
            "user_id": str(user.id),
            "email": user.email,
        },
    )

    return success_response(
        data=response_data.model_dump(),
        message="Token 刷新成功",
        request=request,
    )


@router.post(
    "/logout",
    summary="退出登录",
    description="退出登录，使当前 Token 失效",
    response_model=Response,
)
async def logout(
    request: Request,
    current_user: CurrentUser,
    token_service: Annotated[TokenService, Depends(get_token_service)],
    data: LogoutRequest = None,
) -> Response:
    """
    退出登录

    将当前 Access Token 加入黑名单，可选撤销 Refresh Token

    - **refresh_token**: Refresh Token（可选，提供则同时撤销）
    """
    # 获取当前 Access Token
    # 从请求头中提取
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        # 将 Access Token 加入黑名单
        await token_service.add_to_blacklist(access_token)

    # 如果提供了 Refresh Token，也撤销它
    if data and data.refresh_token:
        payload = decode_token(data.refresh_token)
        if payload:
            await token_service.revoke_refresh_token(
                user_id=payload.sub,
                jti=payload.jti,
            )

    logger.info(
        "User logged out",
        extra={
            "user_id": str(current_user.id),
            "email": current_user.email,
        },
    )

    return success_response(
        data=None,
        message="退出登录成功",
        request=request,
    )


@router.post(
    "/logout/all",
    summary="退出所有设备",
    description="退出所有设备的登录，撤销所有 Token",
    response_model=Response,
)
async def logout_all(
    request: Request,
    current_user: CurrentUser,
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> Response:
    """
    退出所有设备

    撤销用户所有的 Refresh Token，强制所有设备重新登录
    """
    # 获取当前 Access Token 并加入黑名单
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        await token_service.add_to_blacklist(access_token)

    # 撤销所有 Refresh Token
    revoked_count = await token_service.revoke_all_refresh_tokens(
        user_id=str(current_user.id)
    )

    logger.info(
        "User logged out from all devices",
        extra={
            "user_id": str(current_user.id),
            "email": current_user.email,
            "revoked_tokens": revoked_count,
        },
    )

    return success_response(
        data={"revoked_tokens": revoked_count},
        message="已退出所有设备",
        request=request,
    )


@router.get(
    "/me",
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
    response_model=Response[UserOut],
)
async def get_current_user_info(
    request: Request,
    current_user: CurrentUser,
) -> Response:
    """
    获取当前用户信息

    返回当前登录用户的详细信息
    """
    return success_response(
        data=UserOut.model_validate(current_user).model_dump(),
        message="获取成功",
        request=request,
    )