# app/schemas/auth.py
"""
认证相关 Pydantic 模型
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    """注册请求"""

    email: EmailStr = Field(..., description="邮箱")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    tenant_name: Optional[str] = Field(None, max_length=100, description="租户名称（新建租户时）")


class LoginRequest(BaseModel):
    """登录请求"""

    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""

    user: UserOut = Field(description="用户信息")
    # 后续添加 Token 信息
    # access_token: str
    # refresh_token: str
    # token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """注册响应"""

    user: UserOut = Field(description="用户信息")
    tenant_id: str = Field(description="租户ID")
    message: str = Field(default="注册成功", description="消息")