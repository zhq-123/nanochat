# app/schemas/tenant.py
"""
租户相关 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import TenantPlan, TenantStatus


class TenantBase(BaseModel):
    """租户基础模型"""

    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$", description="租户标识")
    description: Optional[str] = Field(None, max_length=500, description="租户描述")


class TenantCreate(TenantBase):
    """创建租户请求"""

    plan: TenantPlan = Field(default=TenantPlan.FREE, description="套餐类型")


class TenantUpdate(BaseModel):
    """更新租户请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    plan: Optional[TenantPlan] = None
    status: Optional[TenantStatus] = None
    settings: Optional[Dict[str, Any]] = None



class TenantOut(TenantBase):
    """租户输出模型"""

    id: UUID = Field(description="租户ID")
    plan: str = Field(description="套餐类型")
    status: str = Field(description="租户状态")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="租户配置")
    quota: Optional[Dict[str, Any]] = Field(default=None, description="配额设置")
    expire_at: Optional[datetime] = Field(default=None, description="过期时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class TenantBrief(BaseModel):
    """租户简要信息"""

    id: UUID
    name: str
    slug: str
    plan: str

    class Config:
        from_attributes = True