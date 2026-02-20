# app/repositories/user_repository.py
"""
用户仓储

提供用户相关的数据访问操作
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            email: 邮箱

        Returns:
            Optional[User]: 用户或 None
        """
        result = await self.session.execute(
            select(User)
            .options(joinedload(User.tenant))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(
        self,
        username: str,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            username: 用户名
            tenant_id: 租户ID（可选）

        Returns:
            Optional[User]: 用户或 None
        """
        query = select(User).where(User.username == username)
        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """
        检查邮箱是否已存在

        Args:
            email: 邮箱

        Returns:
            bool: 是否存在
        """
        return await self.exists(email=email)

    async def username_exists_in_tenant(
        self,
        username: str,
        tenant_id: UUID,
    ) -> bool:
        """
        检查租户内用户名是否已存在

        Args:
            username: 用户名
            tenant_id: 租户ID

        Returns:
            bool: 是否存在
        """
        result = await self.session.execute(
            select(User.id)
            .where(User.username == username)
            .where(User.tenant_id == tenant_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[User]:
        """
        获取租户下的用户列表

        Args:
            tenant_id: 租户ID
            skip: 跳过数量
            limit: 限制数量
            is_active: 是否激活（可选过滤）

        Returns:
            List[User]: 用户列表
        """
        query = (
            select(User)
            .where(User.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_tenant(
        self,
        tenant_id: UUID,
        is_active: Optional[bool] = None,
    ) -> int:
        """
        获取租户下的用户数量

        Args:
            tenant_id: 租户ID
            is_active: 是否激活（可选过滤）

        Returns:
            int: 用户数量
        """
        query = (
            select(func.count())
            .select_from(User)
            .where(User.tenant_id == tenant_id)
        )

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_with_tenant(self, user_id: UUID) -> Optional[User]:
        """
        获取用户（包含租户信息）

        Args:
            user_id: 用户ID

        Returns:
            Optional[User]: 用户或 None
        """
        result = await self.session.execute(
            select(User)
            .options(joinedload(User.tenant))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()