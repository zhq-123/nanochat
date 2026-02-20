# app/schemas/user.py
"""
用户相关 Pydantic 模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.tenant import TenantBrief


class UserBase(BaseModel):
    """用户基础模型"""

    email: EmailStr = Field(..., description="邮箱")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")


class UserCreate(UserBase):
    """创建用户请求"""

    password: str = Field(..., min_length=8, max_length=128, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v[0].isalpha():
            raise ValueError("用户名必须以字母开头")
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v


class UserUpdate(BaseModel):
    """更新用户请求"""

    username: Optional[str] = Field(None, min_length=2, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)


class UserOut(UserBase):
    """用户输出模型"""

    id: str = Field(description="用户ID")
    full_name: Optional[str] = Field(default=None, description="全名")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    phone: Optional[str] = Field(default=None, description="手机号")
    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否超级管理员")
    is_verified: bool = Field(description="邮箱是否验证")
    last_login_at: Optional[datetime] = Field(default=None, description="最后登录时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class UserWithTenant(UserOut):
    """包含租户信息的用户输出"""

    tenant: TenantBrief = Field(description="所属租户")

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    """用户简要信息"""

    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True