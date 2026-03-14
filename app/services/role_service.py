# app/services/role_service.py
"""
角色服务

处理角色相关的业务逻辑
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import BusinessException, ErrorCode, NotFoundException
from app.models.permission import Permission, SYSTEM_PERMISSIONS
from app.models.role import Role
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_role_repository import UserRoleRepository

logger = logging.getLogger(__name__)


# 默认角色配置
DEFAULT_ROLES = {
    "owner": {
        "name": "所有者",
        "description": "租户所有者，拥有所有权限",
        "permissions": ["*:*"],  # 特殊权限，表示所有
        "is_system": True,
    },
    "admin": {
        "name": "管理员",
        "description": "管理员，可管理用户和角色",
        "permissions": [
            "user:*", "role:*",
            "conversation:*", "knowledge_base:*",
            "document:*", "agent:*",
            "tenant:read", "tenant:settings",
        ],
        "is_system": True,
    },
    "member": {
        "name": "成员",
        "description": "普通成员，可使用基础功能",
        "permissions": [
            "conversation:create", "conversation:read", "conversation:update",
            "conversation:delete", "conversation:list",
            "knowledge_base:read", "knowledge_base:list",
            "document:read", "document:list",
            "agent:read", "agent:list", "agent:execute",
        ],
        "is_system": True,
        "is_default": True,
    },
    "viewer": {
        "name": "访客",
        "description": "只读访问权限",
        "permissions": [
            "conversation:read", "conversation:list",
            "knowledge_base:read", "knowledge_base:list",
            "document:read", "document:list",
            "agent:read", "agent:list",
        ],
        "is_system": True,
    },
}


class RoleService:
    """角色服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.role_repo = RoleRepository(session)
        self.permission_repo = PermissionRepository(session)
        self.user_role_repo = UserRoleRepository(session)
        self.user_repo = UserRepository(session)

    async def init_permissions(self) -> int:
        """
        初始化系统权限

        Returns:
            int: 创建的权限数量
        """
        count = await self.permission_repo.init_system_permissions(SYSTEM_PERMISSIONS)
        logger.info(f"Initialized {count} permissions")
        return count

    async def init_tenant_roles(self, tenant_id: UUID) -> List[Role]:
        """
        初始化租户默认角色

        Args:
            tenant_id: 租户ID

        Returns:
            List[Role]: 创建的角色列表
        """
        roles = []
        for code, config in DEFAULT_ROLES.items():
            # 检查是否已存在
            existing = await self.role_repo.get_by_code(code, tenant_id)
            if existing:
                roles.append(existing)
                continue

            # 创建角色
            role = await self.role_repo.create(
                tenant_id=tenant_id,
                code=code,
                name=config["name"],
                description=config["description"],
                is_system=config.get("is_system", False),
                is_default=config.get("is_default", False),
            )

            # 设置权限
            if config["permissions"] != ["*:*"]:
                permissions = await self.permission_repo.get_by_codes(
                    config["permissions"]
                )
                await self.role_repo.set_permissions(role, permissions)

            roles.append(role)

        logger.info(
            f"Initialized tenant roles",
            extra={"tenant_id": str(tenant_id), "role_count": len(roles)},
        )
        return roles

    async def create_role(
        self,
        tenant_id: UUID,
        code: str,
        name: str,
        description: Optional[str] = None,
        permission_codes: Optional[List[str]] = None,
        parent_id: Optional[UUID] = None,
    ) -> Role:
        """
        创建自定义角色

        Args:
            tenant_id: 租户ID
            code: 角色代码
            name: 角色名称
            description: 角色描述
            permission_codes: 权限代码列表
            parent_id: 父角色ID

        Returns:
            Role: 创建的角色
        """
        # 检查代码是否已存在
        if await self.role_repo.code_exists_in_tenant(code, tenant_id):
            raise BusinessException(
                code=ErrorCode.ROLE_ALREADY_EXISTS,
                message=f"角色代码 '{code}' 已存在",
            )

        # 创建角色
        role = await self.role_repo.create(
            tenant_id=tenant_id,
            code=code,
            name=name,
            description=description,
            parent_id=parent_id,
            is_system=False,
            is_default=False,
        )

        # 设置权限
        if permission_codes:
            permissions = await self.permission_repo.get_by_codes(permission_codes)
            await self.role_repo.set_permissions(role, permissions)

        logger.info(
            "Role created",
            extra={
                "role_id": str(role.id),
                "code": code,
                "tenant_id": str(tenant_id),
            },
        )

        return role

    async def update_role(
        self,
        role_id: UUID,
        tenant_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_codes: Optional[List[str]] = None,
    ) -> Role:
        """
        更新角色

        Args:
            role_id: 角色ID
            tenant_id: 租户ID
            name: 角色名称
            description: 角色描述
            permission_codes: 权限代码列表

        Returns:
            Role: 更新后的角色
        """
        role = await self.role_repo.get_with_permissions(role_id)
        if not role:
            raise NotFoundException(
                code=ErrorCode.ROLE_NOT_FOUND,
                resource="角色",
            )

        # 检查是否属于该租户
        if role.tenant_id != tenant_id:
            raise BusinessException(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权修改此角色",
            )

        # 系统角色不允许修改
        if role.is_system:
            raise BusinessException(
                code=ErrorCode.VALIDATION_ERROR,
                message="系统角色不允许修改",
            )

        # 更新基本信息
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description

        # 更新权限
        if permission_codes is not None:
            permissions = await self.permission_repo.get_by_codes(permission_codes)
            await self.role_repo.set_permissions(role, permissions)

        await self.session.flush()
        await self.session.refresh(role)

        logger.info(
            "Role updated",
            extra={"role_id": str(role_id)},
        )

        return role

    async def delete_role(self, role_id: UUID, tenant_id: UUID) -> bool:
        """
        删除角色

        Args:
            role_id: 角色ID
            tenant_id: 租户ID

        Returns:
            bool: 是否成功
        """
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundException(
                code=ErrorCode.ROLE_NOT_FOUND,
                resource="角色",
            )

        # 检查是否属于该租户
        if role.tenant_id != tenant_id:
            raise BusinessException(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权删除此角色",
            )

        # 系统角色不允许删除
        if role.is_system:
            raise BusinessException(
                code=ErrorCode.VALIDATION_ERROR,
                message="系统角色不允许删除",
            )

        # 检查是否有用户使用此角色
        user_count = await self.user_role_repo.count_role_users(role_id)
        if user_count > 0:
            raise BusinessException(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"该角色已分配给 {user_count} 个用户，请先取消分配",
            )

        await self.role_repo.delete(role)

        logger.info(
            "Role deleted",
            extra={"role_id": str(role_id)},
        )

        return True

    async def get_role(self, role_id: UUID) -> Role:
        """
        获取角色详情

        Args:
            role_id: 角色ID

        Returns:
            Role: 角色
        """
        role = await self.role_repo.get_with_permissions(role_id)
        if not role:
            raise NotFoundException(
                code=ErrorCode.ROLE_NOT_FOUND,
                resource="角色",
            )
        return role

    async def get_tenant_roles(
        self,
        tenant_id: UUID,
        include_system: bool = True,
    ) -> List[Role]:
        """
        获取租户的角色列表

        Args:
            tenant_id: 租户ID
            include_system: 是否包含系统角色

        Returns:
            List[Role]: 角色列表
        """
        return await self.role_repo.get_by_tenant(tenant_id, include_system)

    async def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID,
        assigned_by: Optional[UUID] = None,
    ) -> bool:
        """
        为用户分配角色

        Args:
            user_id: 用户ID
            role_id: 角色ID
            tenant_id: 租户ID
            assigned_by: 分配人ID

        Returns:
            bool: 是否成功
        """
        # 检查用户是否存在
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.tenant_id != tenant_id:
            raise NotFoundException(
                code=ErrorCode.USER_NOT_FOUND,
                resource="用户",
            )

        # 检查角色是否存在
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundException(
                code=ErrorCode.ROLE_NOT_FOUND,
                resource="角色",
            )

        # 检查角色是否属于该租户
        if role.tenant_id and role.tenant_id != tenant_id:
            raise BusinessException(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权分配此角色",
            )

        await self.user_role_repo.assign_role(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            assigned_by=assigned_by,
        )

        logger.info(
            "Role assigned to user",
            extra={
                "user_id": str(user_id),
                "role_id": str(role_id),
                "assigned_by": str(assigned_by) if assigned_by else None,
            },
        )

        return True

    async def revoke_role_from_user(
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
        # 检查用户角色数量
        user_roles = await self.user_role_repo.get_user_roles(user_id, tenant_id)
        if len(user_roles) <= 1:
            raise BusinessException(
                code=ErrorCode.VALIDATION_ERROR,
                message="用户至少需要保留一个角色",
            )

        await self.user_role_repo.revoke_role(user_id, role_id, tenant_id)

        logger.info(
            "Role revoked from user",
            extra={
                "user_id": str(user_id),
                "role_id": str(role_id),
            },
        )

        return True

    async def get_user_roles(
        self,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> List[Role]:
        """
        获取用户的角色

        Args:
            user_id: 用户ID
            tenant_id: 租户ID

        Returns:
            List[Role]: 角色列表
        """
        return await self.user_role_repo.get_user_roles(user_id, tenant_id)

    async def get_all_permissions(self) -> List[Permission]:
        """
        获取所有权限

        Returns:
            List[Permission]: 权限列表
        """
        return await self.permission_repo.get_all()

    async def get_permissions_grouped(self) -> dict:
        """
        获取分组的权限

        Returns:
            dict: 分组权限
        """
        return await self.permission_repo.get_all_grouped()