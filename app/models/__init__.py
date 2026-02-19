# app/models/__init__.py
"""
数据模型模块

集中导出所有模型类，便于 Alembic 发现模型
"""

from app.models.base import (
    Base,
    BaseModel,
    SoftDeleteBaseModel,
    SoftDeleteMixin,
    TenantBaseModel,
    TenantMixin,
    TenantSoftDeleteBaseModel,
    TimestampMixin,
    UUIDMixin,
)

__all__ = [
    # 基类
    "Base",
    "BaseModel",
    "TenantBaseModel",
    "SoftDeleteBaseModel",
    "TenantSoftDeleteBaseModel",
    # 混入类
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    # 租户
    "Tenant",
    "TenantPlan",
    "TenantStatus",
    "DEFAULT_QUOTAS",
    # 用户
    "User",
]

from app.models.tenant import TenantPlan, TenantStatus, Tenant, DEFAULT_QUOTAS
from app.models.user import User
