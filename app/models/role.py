# app/models/role.py
"""
角色模型

定义租户内的角色
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Role(BaseModel):
    """
    角色模型

    Attributes:
        tenant_id: 所属租户ID（NULL 表示系统角色）
        code: 角色代码
        name: 角色名称
        description: 角色描述
        is_system: 是否系统内置角色
        is_default: 是否默认角色（新用户自动分配）
        parent_id: 父角色ID（用于角色继承）
    """

    __tablename__ = "roles"

    # ==================== 租户关联 ====================
    tenant_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,  # NULL 表示系统级角色
        index=True,
        comment="租户ID",
    )

    # ==================== 基础信息 ====================
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="角色代码",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="角色名称",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="角色描述",
    )

    # ==================== 状态标识 ====================
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否系统角色",
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否默认角色",
    )

    # ==================== 角色继承 ====================
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        comment="父角色ID",
    )

    # ==================== 关系 ====================
    tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant",
        back_populates="roles",
        lazy="joined",
    )

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )

    parent: Mapped[Optional["Role"]] = relationship(
        "Role",
        remote_side="Role.id",
        back_populates="children",
        lazy="joined",
    )

    children: Mapped[list["Role"]] = relationship(
        "Role",
        back_populates="parent",
        lazy="selectin",
    )

    # ==================== 约束与索引 ====================
    __table_args__ = (
        # 租户内角色代码唯一
        UniqueConstraint("tenant_id", "code", name="uq_role_tenant_code"),
        Index("ix_roles_is_system", "is_system"),
        Index("ix_roles_is_default", "is_default"),
    )

    def __repr__(self) -> str:
        return f"<Role(code={self.code}, name={self.name}, tenant_id={self.tenant_id})>"

    def get_all_permissions(self) -> set:
        """
        获取所有权限（包括继承的权限）

        Returns:
            set: 权限代码集合
        """
        permissions = {p.code for p in self.permissions}

        # 递归获取父角色的权限
        if self.parent:
            permissions.update(self.parent.get_all_permissions())

        return permissions


# 角色-权限关联表
from sqlalchemy import Table, Column, ForeignKey
from app.models.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)