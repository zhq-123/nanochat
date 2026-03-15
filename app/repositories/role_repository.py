# app/repositories/role_repository.py
"""
角色仓储

提供角色相关的数据访问操作
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.role import Role
from app.models.permission import Permission
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """角色仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_code(
        self,
        code: str,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[Role]:
        """
        根据代码获取角色

        Args:
            code: 角色代码
            tenant_id: 租户ID

        Returns:
            Optional[Role]: 角色或 None
        """
        query = select(Role).options(
            selectinload(Role.permissions),
            joinedload(Role.parent),
        ).where(Role.code == code)

        if tenant_id:
            # 查找租户角色或系统角色
            query = query.where(
                or_(
                    Role.tenant_id == tenant_id,
                    Role.tenant_id.is_(None),
                )
            )
        else:
            query = query.where(Role.tenant_id.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_tenant(
        self,
        tenant_id: UUID,
        include_system: bool = True,
    ) -> list[Role]:
        """
        获取租户的角色列表

        Args:
            tenant_id: 租户ID
            include_system: 是否包含系统角色

        Returns:
            list[Role]: 角色列表
        """
        query = select(Role).options(
            selectinload(Role.permissions),
        )

        if include_system:
            query = query.where(
                or_(
                    Role.tenant_id == tenant_id,
                    Role.tenant_id.is_(None),
                )
            )
        else:
            query = query.where(Role.tenant_id == tenant_id)

        query = query.order_by(Role.is_system.desc(), Role.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_permissions(self, role_id: UUID) -> Optional[Role]:
        """
        获取角色（包含权限）

        Args:
            role_id: 角色ID

        Returns:
            Optional[Role]: 角色或 None
        """
        result = await self.session.execute(
            select(Role)
            .options(
                selectinload(Role.permissions),
                joinedload(Role.parent).selectinload(Role.permissions),
            )
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_default_role(self, tenant_id: UUID) -> Optional[Role]:
        """
        获取租户的默认角色

        Args:
            tenant_id: 租户ID

        Returns:
            Optional[Role]: 默认角色或 None
        """
        result = await self.session.execute(
            select(Role)
            .where(Role.tenant_id == tenant_id)
            .where(Role.is_default == True)
        )
        return result.scalar_one_or_none()

    async def code_exists_in_tenant(
        self,
        code: str,
        tenant_id: Optional[UUID],
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """
        检查角色代码是否存在

        Args:
            code: 角色代码
            tenant_id: 租户ID
            exclude_id: 排除的角色ID

        Returns:
            bool: 是否存在
        """
        query = select(Role.id).where(Role.code == code)

        if tenant_id:
            query = query.where(
                or_(
                    Role.tenant_id == tenant_id,
                    Role.tenant_id.is_(None),
                )
            )
        else:
            query = query.where(Role.tenant_id.is_(None))

        if exclude_id:
            query = query.where(Role.id != exclude_id)

        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def add_permissions(
        self,
        role: Role,
        permissions: list[Permission],
    ) -> Role:
        """
        为角色添加权限

        Args:
            role: 角色
            permissions: 权限列表

        Returns:
            Role: 更新后的角色
        """
        for perm in permissions:
            if perm not in role.permissions:
                role.permissions.append(perm)

        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def set_permissions(
        self,
        role: Role,
        permissions: list[Permission],
    ) -> Role:
        """
        设置角色权限（替换现有权限）

        Args:
            role: 角色
            permissions: 权限列表

        Returns:
            Role: 更新后的角色
        """
        role.permissions = permissions
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def remove_permissions(
        self,
        role: Role,
        permissions: list[Permission],
    ) -> Role:
        """
        移除角色权限

        Args:
            role: 角色
            permissions: 权限列表

        Returns:
            Role: 更新后的角色
        """
        for perm in permissions:
            if perm in role.permissions:
                role.permissions.remove(perm)

        await self.session.flush()
        await self.session.refresh(role)
        return role