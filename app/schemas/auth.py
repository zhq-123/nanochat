# app/schemas/auth.py
"""
认证相关 Pydantic 模型
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    """注册请求"""

    email: str = Field(..., description="邮箱")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    tenant_name: Optional[str] = Field(None, max_length=100, description="租户名称（新建租户时）")


class LoginRequest(BaseModel):
    """登录请求"""

    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""

    access_token: str = Field(description="Access Token")
    refresh_token: str = Field(description="Refresh Token")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_in: int = Field(description="Access Token 过期时间（秒）")


class LoginResponse(BaseModel):
    """登录响应"""

    user: UserOut = Field(description="用户信息")
    token: TokenResponse = Field(description="Token 信息")


class RegisterResponse(BaseModel):
    """注册响应"""

    user: UserOut = Field(description="用户信息")
    tenant_id: UUID = Field(description="租户ID")
    token: TokenResponse = Field(description="Token 信息")
    message: str = Field(default="注册成功", description="消息")



class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""

    refresh_token: str = Field(..., description="Refresh Token")


class RefreshTokenResponse(BaseModel):
    """刷新 Token 响应"""

    access_token: str = Field(description="新的 Access Token")
    refresh_token: str = Field(description="新的 Refresh Token")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_in: int = Field(description="Access Token 过期时间（秒）")


class LogoutRequest(BaseModel):
    """退出登录请求"""

    refresh_token: Optional[str] = Field(None, description="Refresh Token（可选）")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")