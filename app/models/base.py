# app/models/base.py
"""
SQLAlchemy 模型基类

提供:
- 通用字段（id, created_at, updated_at）
- 软删除支持
- 多租户支持
- 通用方法
"""
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """
    所有模型的基类

    特性:
    - 异步属性支持 (AsyncAttrs)
    - 自动表名生成
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        自动生成表名

        将 CamelCase 类名转换为 snake_case 表名
        例如: UserProfile -> user_profile
        """
        import re
        name = cls.__name__
        # 在大写字母前添加下划线，然后转小写
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    def to_dict(self) -> dict[str, Any]:
        """
        将模型转换为字典

        Returns:
            dict: 模型属性字典
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TimestampMixin:
    """
    时间戳混入类

    添加 created_at 和 updated_at 字段
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class SoftDeleteMixin:
    """
    软删除混入类

    添加 deleted_at 字段，不实际删除数据
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="删除时间",
    )

    @property
    def is_deleted(self) -> bool:
        """是否已删除"""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """软删除"""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """恢复"""
        self.deleted_at = None


class UUIDMixin:
    """
    UUID 主键混入类

    使用 UUID 作为主键
    """

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("uuid_generate_v7()"),
        comment="主键ID",
    )


class TenantMixin:
    """
    多租户混入类

    添加 tenant_id 字段用于数据隔离
    """

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="租户ID",
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    标准基础模型

    包含:
    - UUID 主键
    - 创建时间
    - 更新时间

    大多数模型应该继承此类
    """

    __abstract__ = True


class TenantBaseModel(BaseModel, TenantMixin):
    """
    多租户基础模型

    包含:
    - UUID 主键
    - 租户ID
    - 创建时间
    - 更新时间

    需要租户隔离的模型应该继承此类
    """

    __abstract__ = True


class SoftDeleteBaseModel(BaseModel, SoftDeleteMixin):
    """
    支持软删除的基础模型

    包含:
    - UUID 主键
    - 创建时间
    - 更新时间
    - 删除时间

    需要软删除的模型应该继承此类
    """

    __abstract__ = True


class TenantSoftDeleteBaseModel(TenantBaseModel, SoftDeleteMixin):
    """
    多租户 + 软删除基础模型

    包含:
    - UUID 主键
    - 租户ID
    - 创建时间
    - 更新时间
    - 删除时间

    需要租户隔离和软删除的模型应该继承此类
    """

    __abstract__ = True
