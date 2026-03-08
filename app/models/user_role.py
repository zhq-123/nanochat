# app/models/user_role.py
"""
用户-角色关联模型

管理用户在租户内的角色分配
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Table, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel

# 简单关联表（多对多）
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class UserRoleAssignment(BaseModel):
    """
    用户角色分配记录（带额外信息的关联）

    用于记录角色分配的详细信息，如分配时间、分配人等

    Attributes:
        user_id: 用户ID
        role_id: 角色ID
        tenant_id: 租户ID
        assigned_by: 分配人ID
    """

    __tablename__ = "user_role_assignments"

    # ==================== 关联信息 ====================
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="角色ID",
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="租户ID",
    )

    # ==================== 分配信息 ====================
    assigned_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="分配人ID",
    )

    # ==================== 关系 ====================
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined",
    )

    role: Mapped["Role"] = relationship(
        "Role",
        lazy="joined",
    )

    assigner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_by],
        lazy="joined",
    )

    # ==================== 约束与索引 ====================
    __table_args__ = (
        # 用户在租户内的角色唯一
        UniqueConstraint("user_id", "role_id", "tenant_id", name="uq_user_role_tenant"),
        Index("ix_user_role_tenant", "tenant_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserRoleAssignment(user_id={self.user_id}, role_id={self.role_id})>"