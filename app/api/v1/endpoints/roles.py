# app/api/v1/endpoints/roles.py
"""
角色接口

提供角色管理相关 API
"""

import logging
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    CurrentUser,
    DBSession,
    require_permissions,
)
from app.models.user import User
from app.schemas import Response
from app.schemas.role import (
    AssignRoleRequest,
    PermissionGroupOut,
    PermissionOut,
    RevokeRoleRequest,
    RoleCreate,
    RoleDetailOut,
    RoleOut,
    RoleUpdate,
    UserRolesOut,
)
from app.services.role_service import RoleService
from app.utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/permissions",
    summary="获取所有权限",
    description="获取系统所有权限列表",
    response_model=Response[List[PermissionGroupOut]],
)
async def get_permissions(
    request: Request,
    current_user: CurrentUser,
    db: DBSession,
) -> Response:
    """获取所有权限（按资源分组）"""
    service = RoleService(db)
    grouped = await service.get_permissions_grouped()

    result = [
        PermissionGroupOut(
            resource=resource,
            permissions=[
                PermissionOut(
                    id=str(p.id),
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    resource=p.resource,
                    action=p.action,
                )
                for p in permissions
            ],
        )
        for resource, permissions in grouped.items()
    ]

    return success_response(
        data=[g.model_dump() for g in result],
        request=request,
    )


@router.get(
    "",
    summary="获取角色列表",
    description="获取当前租户的角色列表",
    response_model=Response[List[RoleOut]],
)
async def list_roles(
    request: Request,
    current_user: Annotated[User, Depends(require_permissions("role:list"))],
    db: DBSession,
    include_system: bool = True,
) -> Response:
    """获取角色列表"""
    service = RoleService(db)
    roles = await service.get_tenant_roles(
        tenant_id=current_user.tenant_id,
        include_system=include_system,
    )

    return success_response(
        data=[
            RoleOut(
                id=str(r.id),
                tenant_id=str(r.tenant_id) if r.tenant_id else None,
                code=r.code,
                name=r.name,
                description=r.description,
                is_system=r.is_system,
                is_default=r.is_default,
                parent_id=str(r.parent_id) if r.parent_id else None,
                created_at=r.created_at,
                updated_at=r.updated_at,
            ).model_dump()
            for r in roles
        ],
        request=request,
    )


@router.post(
    "",
    summary="创建角色",
    description="创建自定义角色",
    response_model=Response[RoleDetailOut],
)
async def create_role(
    request: Request,
    data: RoleCreate,
    current_user: Annotated[User, Depends(require_permissions("role:create"))],
    db: DBSession,
) -> Response:
    """创建角色"""
    service = RoleService(db)
    role = await service.create_role(
        tenant_id=current_user.tenant_id,
        code=data.code,
        name=data.name,
        description=data.description,
        permission_codes=data.permission_codes,
        parent_id=UUID(data.parent_id) if data.parent_id else None,
    )

    return success_response(
        data=RoleDetailOut(
            id=str(role.id),
            tenant_id=str(role.tenant_id) if role.tenant_id else None,
            code=role.code,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            is_default=role.is_default,
            parent_id=str(role.parent_id) if role.parent_id else None,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=[
                PermissionOut(
                    id=str(p.id),
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    resource=p.resource,
                    action=p.action,
                )
                for p in role.permissions
            ],
        ).model_dump(),
        message="角色创建成功",
        request=request,
    )


@router.get(
    "/{role_id}",
    summary="获取角色详情",
    description="获取角色详细信息",
    response_model=Response[RoleDetailOut],
)
async def get_role(
    request: Request,
    role_id: str,
    current_user: Annotated[User, Depends(require_permissions("role:read"))],
    db: DBSession,
) -> Response:
    """获取角色详情"""
    service = RoleService(db)
    role = await service.get_role(UUID(role_id))

    return success_response(
        data=RoleDetailOut(
            id=str(role.id),
            tenant_id=str(role.tenant_id) if role.tenant_id else None,
            code=role.code,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            is_default=role.is_default,
            parent_id=str(role.parent_id) if role.parent_id else None,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=[
                PermissionOut(
                    id=str(p.id),
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    resource=p.resource,
                    action=p.action,
                )
                for p in role.permissions
            ],
        ).model_dump(),
        request=request,
    )


@router.put(
    "/{role_id}",
    summary="更新角色",
    description="更新角色信息",
    response_model=Response[RoleDetailOut],
)
async def update_role(
    request: Request,
    role_id: str,
    data: RoleUpdate,
    current_user: Annotated[User, Depends(require_permissions("role:update"))],
    db: DBSession,
) -> Response:
    """更新角色"""
    service = RoleService(db)
    role = await service.update_role(
        role_id=UUID(role_id),
        tenant_id=current_user.tenant_id,
        name=data.name,
        description=data.description,
        permission_codes=data.permission_codes,
    )

    return success_response(
        data=RoleDetailOut(
            id=str(role.id),
            tenant_id=str(role.tenant_id) if role.tenant_id else None,
            code=role.code,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            is_default=role.is_default,
            parent_id=str(role.parent_id) if role.parent_id else None,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=[
                PermissionOut(
                    id=str(p.id),
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    resource=p.resource,
                    action=p.action,
                )
                for p in role.permissions
            ],
        ).model_dump(),
        message="角色更新成功",
        request=request,
    )


@router.delete(
    "/{role_id}",
    summary="删除角色",
    description="删除自定义角色",
    response_model=Response,
)
async def delete_role(
    request: Request,
    role_id: str,
    current_user: Annotated[User, Depends(require_permissions("role:delete"))],
    db: DBSession,
) -> Response:
    """删除角色"""
    service = RoleService(db)
    await service.delete_role(
        role_id=UUID(role_id),
        tenant_id=current_user.tenant_id,
    )

    return success_response(
        data=None,
        message="角色删除成功",
        request=request,
    )


@router.post(
    "/assign",
    summary="分配角色",
    description="为用户分配角色",
    response_model=Response,
)
async def assign_role(
    request: Request,
    data: AssignRoleRequest,
    current_user: Annotated[User, Depends(require_permissions("role:assign"))],
    db: DBSession,
) -> Response:
    """分配角色"""
    service = RoleService(db)
    await service.assign_role_to_user(
        user_id=UUID(data.user_id),
        role_id=UUID(data.role_id),
        tenant_id=current_user.tenant_id,
        assigned_by=current_user.id,
    )

    return success_response(
        data=None,
        message="角色分配成功",
        request=request,
    )


@router.post(
    "/revoke",
    summary="撤销角色",
    description="撤销用户的角色",
    response_model=Response,
)
async def revoke_role(
    request: Request,
    data: RevokeRoleRequest,
    current_user: Annotated[User, Depends(require_permissions("role:assign"))],
    db: DBSession,
) -> Response:
    """撤销角色"""
    service = RoleService(db)
    await service.revoke_role_from_user(
        user_id=UUID(data.user_id),
        role_id=UUID(data.role_id),
        tenant_id=current_user.tenant_id,
    )

    return success_response(
        data=None,
        message="角色撤销成功",
        request=request,
    )


@router.get(
    "/users/{user_id}/roles",
    summary="获取用户角色",
    description="获取指定用户的角色列表",
    response_model=Response[UserRolesOut],
)
async def get_user_roles(
    request: Request,
    user_id: str,
    current_user: Annotated[User, Depends(require_permissions("role:read"))],
    db: DBSession,
) -> Response:
    """获取用户角色"""
    service = RoleService(db)
    roles = await service.get_user_roles(
        user_id=UUID(user_id),
        tenant_id=current_user.tenant_id,
    )

    return success_response(
        data=UserRolesOut(
            user_id=user_id,
            roles=[
                {
                    "id": str(r.id),
                    "code": r.code,
                    "name": r.name,
                    "is_system": r.is_system,
                }
                for r in roles
            ],
        ).model_dump(),
        request=request,
    )