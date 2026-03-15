# app/core/permissions.py
"""
权限装饰器模块

提供装饰器方式的权限检查
"""
import functools
import logging
from typing import Callable

from app.core import AuthorizationException, ErrorCode
from app.models import User

logger = logging.getLogger(__name__)


def check_permission(
        permissions: str | list[str],
        require_all: bool = True,
):
    """
    权限检查装饰器

    用于装饰服务层方法，在执行前检查权限

    用法:
        class MyService:
            @check_permission("user:create")
            async def create_user(self, user: User, data: dict):
                ...

            @check_permission(["user:read", "user:list"], require_all=False)
            async def get_users(self, user: User):
                ...

    Args:
        permissions: 需要的权限（单个或列表）
        require_all: 是否需要全部权限

    Returns:
        装饰器函数
    """
    if isinstance(permissions, str):
        permissions = [permissions]

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中查找 User 对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break

            if user is None:
                user = kwargs.get("user") or kwargs.get("current_user")

            if user is None:
                raise ValueError(
                    f"Function {func.__name__} decorated with @check_permission "
                    "must have a User parameter"
                )

            # 检查权限
            if require_all:
                has_permission = user.has_all_permissions(*permissions)
            else:
                has_permission = user.has_any_permission(*permissions)

            if not has_permission:
                logger.warning(
                    "Permission denied",
                    extra={
                        "user_id": str(user.id),
                        "required_permissions": permissions,
                        "function": func.__name__,
                    },
                )
                raise AuthorizationException(
                    code=ErrorCode.PERMISSION_DENIED,
                    message="权限不足",
                    required_permissions=permissions,
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def check_resource_permission(
    permission: str,
    resource_type: str,
    owner_field: str = "user_id",
):
    """
    资源权限检查装饰器

    检查用户是否有权访问指定资源

    用法:
        class ConversationService:
            @check_resource_permission(
                permission="conversation:read",
                resource_type="conversation",
                owner_field="user_id",
            )
            async def get_conversation(
                self,
                user: User,
                conversation: Conversation,
            ):
                ...

    Args:
        permission: 管理权限
        resource_type: 资源类型
        owner_field: 资源中表示所有者的字段名

    Returns:
        装饰器函数
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取 User
            user = None
            resource = None

            for arg in args:
                if isinstance(arg, User):
                    user = arg
                elif hasattr(arg, owner_field):
                    resource = arg

            if user is None:
                user = kwargs.get("user") or kwargs.get("current_user")

            if resource is None:
                resource = kwargs.get(resource_type)

            if user is None:
                raise ValueError(
                    f"Function {func.__name__} must have a User parameter"
                )

            # 超级管理员直接通过
            if user.is_superuser:
                return await func(*args, **kwargs)

            # 有管理权限直接通过
            if user.has_permission(permission):
                return await func(*args, **kwargs)

            # 检查是否是所有者
            if resource is not None:
                resource_owner_id = getattr(resource, owner_field, None)
                if resource_owner_id and str(user.id) == str(resource_owner_id):
                    return await func(*args, **kwargs)

            logger.warning(
                "Resource permission denied",
                extra={
                    "user_id": str(user.id),
                    "resource_type": resource_type,
                    "permission": permission,
                    "function": func.__name__,
                },
            )
            raise AuthorizationException(
                code=ErrorCode.PERMISSION_DENIED,
                message=f"无权访问此{resource_type}",
            )

        return wrapper

    return decorator