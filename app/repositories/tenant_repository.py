# app/repositories/tenant_repository.py
"""
租户仓储

提供租户相关的数据访问操作
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """租户仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        根据 slug 获取租户

        Args:
            slug: 租户标识

        Returns:
            Optional[Tenant]: 租户或 None
        """
        result = await self.session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        """
        检查 slug 是否已存在

        Args:
            slug: 租户标识

        Returns:
            bool: 是否存在
        """
        return await self.exists(slug=slug)