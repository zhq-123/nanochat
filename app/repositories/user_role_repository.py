# app/repositories/user_role_repository.py
"""
用户角色仓储

提供用户角色关联的数据访问操作
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User
from app.models.user_role import user_roles, UserRoleAssignment
from app.repositories.base import BaseRepository


class UserRoleRepository(BaseRepository[UserRoleAssignment]):
    """用户角色仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(UserRoleAssignment, session)

    async def get_user_roles(
        self,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> list[Role]:
        """
        获取用户的角色

        Args:
            user_id: 用户ID
            tenant_id: 租户ID（可选）

        Returns:
            list[Role]: 角色列表
        """
        query = (
            select(Role)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(user_roles.c.user_id == user_id)
            .options(selectinload(Role.permissions))
        )

        if tenant_id:
            query = query.where(
                (Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None))
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID,
        assigned_by: Optional[UUID] = None,
    ) -> UserRoleAssignment:
        """
        分配角色给用户

        Args:
            user_id: 用户ID
            role_id: 角色ID
            tenant_id: 租户ID
            assigned_by: 分配人ID

        Returns:
            UserRoleAssignment: 分配记录
        """
        # 检查是否已分配
        existing = await self.get_assignment(user_id, role_id, tenant_id)
        if existing:
            return existing

        assignment = await self.create(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            assigned_by=assigned_by,
        )

        # 同时更新 user_roles 关联表
        await self.session.execute(
            user_roles.insert().values(user_id=user_id, role_id=role_id)
        )

        return assignment

    async def revoke_role(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID,
    ) -> bool:
        """
        撤销用户的角色

        Args:
            user_id: 用户ID
            role_id: 角色ID
            tenant_id: 租户ID

        Returns:
            bool: 是否成功
        """
        # 删除分配记录
        await self.session.execute(
            delete(UserRoleAssignment).where(
                and_(
                    UserRoleAssignment.user_id == user_id,
                    UserRoleAssignment.role_id == role_id,
                    UserRoleAssignment.tenant_id == tenant_id,
                )
            )
        )

        # 删除 user_roles 关联
        await self.session.execute(
            delete(user_roles).where(
                and_(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_id,
                )
            )
        )

        await self.session.flush()
        return True

    async def get_assignment(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID,
    ) -> Optional[UserRoleAssignment]:
        """
        获取角色分配记录

        Args:
            user_id: 用户ID
            role_id: 角色ID
            tenant_id: 租户ID

        Returns:
            Optional[UserRoleAssignment]: 分配记录或 None
        """
        result = await self.session.execute(
            select(UserRoleAssignment).where(
                and_(
                    UserRoleAssignment.user_id == user_id,
                    UserRoleAssignment.role_id == role_id,
                    UserRoleAssignment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_role_users(
        self,
        role_id: UUID,
        tenant_id: UUID,
    ) -> list[User]:
        """
        获取拥有指定角色的用户

        Args:
            role_id: 角色ID
            tenant_id: 租户ID

        Returns:
            list[User]: 用户列表
        """
        result = await self.session.execute(
            select(User)
            .join(user_roles, User.id == user_roles.c.user_id)
            .where(user_roles.c.role_id == role_id)
            .where(User.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def count_role_users(self, role_id: UUID) -> int:
        """
        统计拥有指定角色的用户数量

        Args:
            role_id: 角色ID

        Returns:
            int: 用户数量
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count())
            .select_from(user_roles)
            .where(user_roles.c.role_id == role_id)
        )
        return result.scalar() or 0