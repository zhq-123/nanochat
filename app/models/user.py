# app/models/user.py
"""
用户模型

用户是系统的核心实体，属于某个租户
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Index, DateTime, Boolean, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models import BaseModel


class User(BaseModel):
    """
    用户模型

    Attributes:
       tenant_id: 所属租户ID
       email: 邮箱（唯一）
       username: 用户名
       hashed_password: 哈希密码
       full_name: 全名
       avatar_url: 头像URL
       is_active: 是否激活
       is_superuser: 是否超级管理员
       is_verified: 邮箱是否验证
       last_login_at: 最后登录时间
       last_login_ip: 最后登录IP
    """

    __tablename__ = "users"

    # ==================== 租户关联 ====================
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="租户ID",
    )

    # ==================== 认证信息 ====================
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱",
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="用户名",
    )

    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,  # OAuth 用户可能没有密码
        comment="哈希密码",
    )

    # ==================== 个人信息 ====================
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="全名",
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="头像URL",
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="手机号",
    )

    # ==================== 状态标识 ====================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否超级管理员",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="邮箱是否验证",
    )

    # ==================== 登录信息 ====================
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间",
    )

    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="最后登录IP",
    )

    # ==================== 关系 ====================
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
        lazy="joined",
    )

    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    # ==================== 权限方法 ====================
    def get_permissions(self) -> set:
        """
        获取用户所有权限

        Returns:
            set: 权限代码集合
        """
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_all_permissions())
        return permissions

    def has_permission(self, permission_code: str) -> bool:
        """
        检查用户是否有指定权限

        Args:
            permission_code: 权限代码

        Returns:
            bool: 是否有权限
        """
        # 超级管理员拥有所有权限
        if self.is_superuser:
            return True

        permissions = self.get_permissions()

        # 检查完全匹配
        if permission_code in permissions:
            return True

        # 检查通配符匹配
        # *:* 表示所有权限
        if "*:*" in permissions:
            return True

        # resource:* 表示该资源的所有操作
        resource = permission_code.split(":")[0]
        if f"{resource}:*" in permissions:
            return True

        return False

    def has_any_permission(self, *permission_codes: str) -> bool:
        """
        检查用户是否有任一权限

        Args:
            *permission_codes: 权限代码列表

        Returns:
            bool: 是否有任一权限
        """
        return any(self.has_permission(code) for code in permission_codes)

    def has_all_permissions(self, *permission_codes: str) -> bool:
        """
        检查用户是否有全部权限

        Args:
            *permission_codes: 权限代码列表

        Returns:
            bool: 是否有全部权限
        """
        return all(self.has_permission(code) for code in permission_codes)

    # ==================== 索引 ====================
    __table_args__ = (
        # 租户内用户名唯一
        Index("ix_users_tenant_username", "tenant_id", "username", unique=True),
        # 租户内邮箱唯一（实际已通过 email unique 保证全局唯一）
        Index("ix_users_tenant_email", "tenant_id", "email"),
        # 状态索引
        Index("ix_users_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
