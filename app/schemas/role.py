# app/schemas/role.py
"""
角色相关 Pydantic 模型
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PermissionOut(BaseModel):
    """权限输出"""

    id: str = Field(description="权限ID")
    code: str = Field(description="权限代码")
    name: str = Field(description="权限名称")
    description: Optional[str] = Field(default=None, description="权限描述")
    resource: str = Field(description="资源类型")
    action: str = Field(description="操作类型")

    class Config:
        from_attributes = True


class PermissionGroupOut(BaseModel):
    """权限分组输出"""

    resource: str = Field(description="资源类型")
    permissions: List[PermissionOut] = Field(description="权限列表")


class RoleBase(BaseModel):
    """角色基础模型"""

    code: str = Field(..., min_length=1, max_length=50, description="角色代码")
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")


class RoleCreate(RoleBase):
    """创建角色请求"""

    permission_codes: Optional[List[str]] = Field(
        default=None,
        description="权限代码列表",
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="父角色ID",
    )


class RoleUpdate(BaseModel):
    """更新角色请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permission_codes: Optional[List[str]] = Field(default=None)


class RoleOut(RoleBase):
    """角色输出"""

    id: str = Field(description="角色ID")
    tenant_id: Optional[str] = Field(default=None, description="租户ID")
    is_system: bool = Field(description="是否系统角色")
    is_default: bool = Field(description="是否默认角色")
    parent_id: Optional[str] = Field(default=None, description="父角色ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class RoleDetailOut(RoleOut):
    """角色详情输出（包含权限）"""

    permissions: List[PermissionOut] = Field(
        default=[],
        description="权限列表",
    )


class RoleBrief(BaseModel):
    """角色简要信息"""

    id: str
    code: str
    name: str
    is_system: bool

    class Config:
        from_attributes = True


class AssignRoleRequest(BaseModel):
    """分配角色请求"""

    user_id: str = Field(..., description="用户ID")
    role_id: str = Field(..., description="角色ID")


class RevokeRoleRequest(BaseModel):
    """撤销角色请求"""

    user_id: str = Field(..., description="用户ID")
    role_id: str = Field(..., description="角色ID")


class UserRolesOut(BaseModel):
    """用户角色输出"""

    user_id: str = Field(description="用户ID")
    roles: List[RoleBrief] = Field(description="角色列表")