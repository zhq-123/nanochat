# app/repositories/permission_repository.py
"""
权限仓储

提供权限相关的数据访问操作
"""
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission
from app.repositories import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    """权限仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session)

    async def get_by_code(self, code: str) -> Optional[Permission]:
        """
        根据代码获取权限

        Args:
            code: 权限代码

        Returns:
            Optional[Permission]: 权限或 None
        """
        result = await self.session.execute(select(Permission).where(Permission.code == code))
        return result.scalar_one_or_none()

    async def get_by_codes(self, codes: list[str]) -> list[Permission]:
        """
        根据代码列表获取权限

        Args:
            codes: 权限代码列表

        Returns:
            list[Permission]: 权限列表
        """
        result = await self.session.execute(
            select(Permission).where(Permission.code.in_(codes))
        )
        return list(result.scalars().all())

    async def get_by_resource(self, resource: str) -> list[Permission]:
        """
        获取资源的所有权限

        Args:
            resource: 资源类型

        Returns:
            list[Permission]: 权限列表
        """
        result = await self.session.execute(
            select(Permission)
            .where(Permission.resource == resource)
            .order_by(Permission.action)
        )
        return list(result.scalars().all())

    async def get_all_grouped(self) -> dict:
        """
        获取所有权限（按资源分组）

        Returns:
            dict: {resource: [permissions]}
        """
        result = await self.session.execute(
            select(Permission).order_by(Permission.resource, Permission.action)
        )
        permissions = result.scalars().all()

        grouped = {}
        for perm in permissions:
            if perm.resource not in grouped:
                grouped[perm.resource] = []
            grouped[perm.resource].append(perm)

        return grouped

    async def init_system_permissions(self, permissions_data: list[dict]) -> int:
        """
        初始化系统权限

        Args:
            permissions_data: 权限数据列表

        Returns:
            int: 创建的权限数量
        """
        created = 0
        for perm_data in permissions_data:
            existing = await self.get_by_code(perm_data["code"])
            if not existing:
                await self.create(**perm_data)
                created += 1
        return created