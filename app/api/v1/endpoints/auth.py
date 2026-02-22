# app/api/v1/endpoints/auth.py
"""
认证接口

提供用户注册、登录等认证相关 API
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.deps import get_db
from app.db import get_async_session
from app.schemas import RegisterResponse, RegisterRequest, Response, UserOut, LoginResponse, LoginRequest
from app.services import UserService
from app.utils import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP"""
    # 优先从代理头获取
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 如果前面的头都没有，说明请求是直接连接到服务器的（没有代理）
    if request.client:
        return request.client.host

    return "unknown"


@router.post(
    "/register",
    summary="用户注册",
    description="新用户注册，同时创建租户",
    response_model=Response[RegisterResponse],
)
async def register(
    request: Request,
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """
    用户注册

    创建新用户和对应的租户

    - **email**: 邮箱（唯一）
    - **username**: 用户名（2-50字符）
    - **password**: 密码（至少8字符，包含大小写字母和数字）
    - **full_name**: 全名（可选）
    - **tenant_name**: 租户名称（可选，默认使用"用户名的工作空间"）
    """
    service = UserService(db)
    user, tenant = await service.register(data)

    response_data = RegisterResponse(
        user=UserOut.model_validate(user),
        tenant_id=tenant.id,
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
    description="使用邮箱和密码登录",
    response_model=Response[LoginResponse],
)
async def login(
    request: Request,
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """
    用户登录

    使用邮箱和密码进行身份验证

    - **email**: 注册邮箱
    - **password**: 密码

    返回用户信息（后续会包含 Token）
    """
    client_ip = _get_client_ip(request)

    service = UserService(db)
    user = await service.authenticate(data, ip_address=client_ip)

    response_data = LoginResponse(
        user=UserOut.model_validate(user),
    )

    return success_response(
        data=response_data.model_dump(),
        message="登录成功",
        request=request,
    )
