# app/models/user.py
"""
用户模型

用户是系统的核心实体，属于某个租户
"""
from datetime import datetime
from typing import Optional
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
