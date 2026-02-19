# app/models/tenant.py
"""
租户模型

租户是系统的顶级实体，用于：
- 数据隔离
- 配额管理
- 计费单元
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, Index, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel


class TenantPlan(str, Enum):
    """租户套餐"""

    FREE = "free"           # 免费版
    BASIC = "basic"         # 基础版
    PRO = "pro"             # 专业版
    ENTERPRISE = "enterprise"  # 企业版


class TenantStatus(str, Enum):
    """租户状态"""

    ACTIVE = "active"       # 正常
    SUSPENDED = "suspended"  # 暂停
    EXPIRED = "expired"     # 过期


class Tenant(BaseModel):
    """
    租户模型

    Attributes:
        name: 租户名称
        slug: 租户标识（URL友好）
        description: 租户描述
        plan: 套餐类型
        status: 租户状态
        settings: 租户配置（JSON）
        quota: 配额设置（JSON）
        expire_at: 过期时间
    """

    __tablename__ = "tenants"

  # ==================== 基础信息 ====================
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="租户名称",
    )

    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="租户标识",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="租户描述",
    )

    # ==================== 套餐与状态 ====================
    plan: Mapped[str] = mapped_column(
        String(20),
        default=TenantPlan.FREE.value,
        nullable=False,
        comment="套餐类型",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=TenantStatus.ACTIVE.value,
        nullable=False,
        index=True,
        comment="租户状态",
    )

    # ==================== 配置信息 ====================
    settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="租户配置",
    )

    quota: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="配额设置",
    )

    # ==================== 时间信息 ====================
    expire_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="过期时间",
    )

    # ==================== 关系 ====================
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        lazy="selectin",
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index("ix_tenants_status_plan", "status", "plan"),
    )

    # ==================== 属性方法 ====================
    @property
    def is_active(self) -> bool:
        """是否为活跃状态"""
        return self.status == TenantStatus.ACTIVE.value

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expire_at is None:
            return False
        return datetime.utcnow() > self.expire_at

    def get_quota(self, key: str, default: int = 0) -> int:
        """获取配额值"""
        if self.quota is None:
            return default
        return self.quota.get(key, default)

    def get_setting(self, key: str, default=None):
        """获取配置值"""
        if self.settings is None:
            return default
        return self.settings.get(key, default)

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, plan={self.plan})>"


# 默认配额配置
DEFAULT_QUOTAS = {
    TenantPlan.FREE: {
        "max_users": 3,
        "max_conversations": 100,
        "max_messages_per_day": 50,
        "max_knowledge_bases": 1,
        "max_documents": 10,
        "max_document_size_mb": 10,
        "max_agents": 1,
    },
    TenantPlan.BASIC: {
        "max_users": 10,
        "max_conversations": 1000,
        "max_messages_per_day": 500,
        "max_knowledge_bases": 5,
        "max_documents": 100,
        "max_document_size_mb": 50,
        "max_agents": 5,
    },
    TenantPlan.PRO: {
        "max_users": 50,
        "max_conversations": 10000,
        "max_messages_per_day": 5000,
        "max_knowledge_bases": 20,
        "max_documents": 500,
        "max_document_size_mb": 100,
        "max_agents": 20,
    },
    TenantPlan.ENTERPRISE: {
        "max_users": -1,  # 无限制
        "max_conversations": -1,
        "max_messages_per_day": -1,
        "max_knowledge_bases": -1,
        "max_documents": -1,
        "max_document_size_mb": 500,
        "max_agents": -1,
    },
}