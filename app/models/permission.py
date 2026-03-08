# app/models/permission.py
"""
权限模型

定义系统中的所有权限
"""
from typing import List, Optional

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.models import BaseModel


class Permission(BaseModel):
    """
    权限模型

    Attributes:
        code: 权限代码（如 user:create）
        name: 权限名称
        description: 权限描述
        resource: 资源类型
        action: 操作类型
    """

    __tablename__ = "permissions"

    # ==================== 基础信息 ====================
    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="权限代码",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="权限名称",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="权限描述",
    )

    # ==================== 权限分类 ====================
    resource: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="资源类型",
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="操作类型",
    )

    # ==================== 关系 ====================
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index("ix_permissions_resource_action", "resource", "action"),
    )

    def __repr__(self) -> str:
        return f"<Permission(code={self.code}, name={self.name})>"


# 系统预定义权限
SYSTEM_PERMISSIONS = [
    # 用户管理
    {"code": "user:create", "name": "创建用户", "resource": "user", "action": "create"},
    {"code": "user:read", "name": "查看用户", "resource": "user", "action": "read"},
    {"code": "user:update", "name": "更新用户", "resource": "user", "action": "update"},
    {"code": "user:delete", "name": "删除用户", "resource": "user", "action": "delete"},
    {"code": "user:list", "name": "用户列表", "resource": "user", "action": "list"},

    # 角色管理
    {"code": "role:create", "name": "创建角色", "resource": "role", "action": "create"},
    {"code": "role:read", "name": "查看角色", "resource": "role", "action": "read"},
    {"code": "role:update", "name": "更新角色", "resource": "role", "action": "update"},
    {"code": "role:delete", "name": "删除角色", "resource": "role", "action": "delete"},
    {"code": "role:list", "name": "角色列表", "resource": "role", "action": "list"},
    {"code": "role:assign", "name": "分配角色", "resource": "role", "action": "assign"},

    # 对话管理
    {"code": "conversation:create", "name": "创建对话", "resource": "conversation", "action": "create"},
    {"code": "conversation:read", "name": "查看对话", "resource": "conversation", "action": "read"},
    {"code": "conversation:update", "name": "更新对话", "resource": "conversation", "action": "update"},
    {"code": "conversation:delete", "name": "删除对话", "resource": "conversation", "action": "delete"},
    {"code": "conversation:list", "name": "对话列表", "resource": "conversation", "action": "list"},

    # 知识库管理
    {"code": "knowledge_base:create", "name": "创建知识库", "resource": "knowledge_base", "action": "create"},
    {"code": "knowledge_base:read", "name": "查看知识库", "resource": "knowledge_base", "action": "read"},
    {"code": "knowledge_base:update", "name": "更新知识库", "resource": "knowledge_base", "action": "update"},
    {"code": "knowledge_base:delete", "name": "删除知识库", "resource": "knowledge_base", "action": "delete"},
    {"code": "knowledge_base:list", "name": "知识库列表", "resource": "knowledge_base", "action": "list"},

    # 文档管理
    {"code": "document:create", "name": "上传文档", "resource": "document", "action": "create"},
    {"code": "document:read", "name": "查看文档", "resource": "document", "action": "read"},
    {"code": "document:update", "name": "更新文档", "resource": "document", "action": "update"},
    {"code": "document:delete", "name": "删除文档", "resource": "document", "action": "delete"},
    {"code": "document:list", "name": "文档列表", "resource": "document", "action": "list"},

    # Agent 管理
    {"code": "agent:create", "name": "创建Agent", "resource": "agent", "action": "create"},
    {"code": "agent:read", "name": "查看Agent", "resource": "agent", "action": "read"},
    {"code": "agent:update", "name": "更新Agent", "resource": "agent", "action": "update"},
    {"code": "agent:delete", "name": "删除Agent", "resource": "agent", "action": "delete"},
    {"code": "agent:list", "name": "Agent列表", "resource": "agent", "action": "list"},
    {"code": "agent:execute", "name": "执行Agent", "resource": "agent", "action": "execute"},

    # 租户管理
    {"code": "tenant:read", "name": "查看租户", "resource": "tenant", "action": "read"},
    {"code": "tenant:update", "name": "更新租户", "resource": "tenant", "action": "update"},
    {"code": "tenant:settings", "name": "租户设置", "resource": "tenant", "action": "settings"},
]