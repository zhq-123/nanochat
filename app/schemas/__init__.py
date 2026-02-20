# app/schemas/__init__.py
"""
Pydantic 模型模块

导出所有 Schema
"""

from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.schemas.response import (
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
    Response,
    SuccessResponse,
)
from app.schemas.tenant import TenantBrief, TenantCreate, TenantOut, TenantUpdate
from app.schemas.user import UserBrief, UserCreate, UserOut, UserUpdate, UserWithTenant

__all__ = [
    # 响应模型
    "Response",
    "ErrorResponse",
    "ErrorDetail",
    "PaginatedResponse",
    "PaginationMeta",
    "SuccessResponse",
    # 租户
    "TenantCreate",
    "TenantUpdate",
    "TenantOut",
    "TenantBrief",
    # 用户
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "UserBrief",
    "UserWithTenant",
    # 认证
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
]