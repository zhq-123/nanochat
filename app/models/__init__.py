# app/models/__init__.py
"""
数据模型模块
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
from app.models.tenant import DEFAULT_QUOTAS, Tenant, TenantPlan, TenantStatus
from app.models.user import User
from app.models.permission import Permission, SYSTEM_PERMISSIONS
from app.models.role import Role, role_permissions
from app.models.user_role import UserRoleAssignment, user_roles

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
    # 权限
    "Permission",
    "SYSTEM_PERMISSIONS",
    # 角色
    "Role",
    "role_permissions",
    # 用户角色
    "UserRoleAssignment",
    "user_roles",
]