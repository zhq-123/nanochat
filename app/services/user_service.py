# app/services/user_service.py
"""
用户服务

处理用户相关的业务逻辑
"""
import logging
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import BusinessException, ErrorCode, ValidationException, AuthenticationException, NotFoundException
from app.core.security import hash_password, check_password_strength, verify_password
from app.models import User, Tenant, TenantPlan, DEFAULT_QUOTAS
from app.repositories import UserRepository, TenantRepository
from app.schemas import RegisterRequest, LoginRequest

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""

    def __init__(self, session: AsyncSession):
        """
        初始化服务

        Args:
            session: 数据库会话
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.tenant_repo = TenantRepository(session)

    async def register(
            self,
            data: RegisterRequest,
            create_tenant: bool = True,
    ) -> tuple[User, Tenant]:
        """
        用户注册

        Args:
            data: 注册请求数据
            create_tenant: 是否创建新租户

        Returns:
            tuple: (用户, 租户)

        Raises:
            ValidationException: 参数校验失败
            BusinessException: 业务规则违反
        """
        # 1. 检查邮箱是否已存在
        if await self.user_repo.email_exists(data.email):
            raise BusinessException(
                code=ErrorCode.EMAIL_ALREADY_EXISTS,
                message="该邮箱已被注册",
            )

        # 2. 检查密码强度
        is_valid, error_msg = check_password_strength(data.password)
        if not is_valid:
            raise ValidationException(
                message=error_msg,
                errors=[{"field": "password", "message": error_msg}],
            )

        # 3. 创建或获取租户
        if create_tenant:
            tenant_name = data.tenant_name or f"{data.username}的工作空间"
            tenant_slug = self._generate_tenant_slug(data.username)
            tenant = await self._create_tenant(tenant_name, tenant_slug)
        else:
            # 加入默认租户
            raise BusinessException(
                code=ErrorCode.VALIDATION_ERROR,
                message="当前必须创建新租户",
            )

        # 4. 检查租户内用户名是否重复
        if await self.user_repo.username_exists_in_tenant(data.username, tenant.id):
            raise BusinessException(
                code=ErrorCode.USER_ALREADY_EXISTS,
                message="该用户名在此租户下已存在",
            )

        # 5. 创建用户
        user = await self.user_repo.create(
            tenant_id=tenant.id,
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            is_active=True,
            is_superuser=True,  # 租户创建者默认为超级管理员
            is_verified=False,
        )

        logger.info(
            "User registered",
            extra={
                "user_id": str(user.id),
                "email": user.email,
                "tenant_id": str(tenant.id),
            },
        )

        return user, tenant

    async def authenticate(
            self,
            data: LoginRequest,
            ip_address: Optional[str] = None,
    ) -> User:
        """
        用户认证（登录）

        Args:
            data: 登录请求数据
            ip_address: 客户端IP

        Returns:
            User: 认证成功的用户

        Raises:
            AuthenticationException: 认证失败
        """
        # 1. 根据邮箱查找用户
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            logger.warning(
                "Login failed: user not found",
                extra={"email": data.email, "ip": ip_address},
            )
            raise AuthenticationException(
                code=ErrorCode.PASSWORD_INCORRECT,
                message="邮箱或密码错误",
            )

        # 2. 验证密码
        if not user.hashed_password or not verify_password(
                data.password, user.hashed_password
        ):
            logger.warning(
                "Login failed: wrong password",
                extra={"email": data.email, "ip": ip_address},
            )
            raise AuthenticationException(
                code=ErrorCode.PASSWORD_INCORRECT,
                message="邮箱或密码错误",
            )

        # 3. 检查用户状态
        if not user.is_active:
            raise AuthenticationException(
                code=ErrorCode.ACCOUNT_DISABLED,
                message="账号已被禁用",
            )

        # 4. 检查租户状态
        if not user.tenant.is_active:
            raise AuthenticationException(
                code=ErrorCode.TENANT_DISABLED,
                message="所属租户已被禁用",
            )

        # 5. 更新登录信息
        await self.user_repo.update(
            user,
            last_login_at=datetime.utcnow(),
            last_login_ip=ip_address,
        )

        logger.info(
            "User logged in",
            extra={
                "user_id": str(user.id),
                "email": user.email,
                "ip": ip_address,
            },
        )

        return user

    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        根据 ID 获取用户

        Args:
            user_id: 用户ID

        Returns:
            User: 用户

        Raises:
            NotFoundException: 用户不存在
        """
        user = await self.user_repo.get_with_tenant(user_id)
        if not user:
            raise NotFoundException(
                code=ErrorCode.USER_NOT_FOUND,
                resource="用户",
            )
        return user

    async def get_user_by_email(self, email: str) -> User:
        """
        根据邮箱获取用户

        Args:
            email: 邮箱

        Returns:
            User: 用户

        Raises:
            NotFoundException: 用户不存在
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundException(
                code=ErrorCode.USER_NOT_FOUND,
                resource="用户",
            )
        return user

    async def _create_tenant(self, name: str, slug: str) -> Tenant:
        """
        创建租户

        Args:
            name: 租户名称
            slug: 租户标识

        Returns:
            Tenant: 创建的租户
        """
        # 确保 slug 唯一
        original_slug = slug
        counter = 1
        while await self.tenant_repo.slug_exists(slug):
            slug = f"{original_slug}-{counter}"
            counter += 1

        tenant = await self.tenant_repo.create(
            name=name,
            slug=slug,
            plan=TenantPlan.FREE.value,
            quota=DEFAULT_QUOTAS[TenantPlan.FREE],
        )

        logger.info(
            "Tenant created",
            extra={
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "slug": tenant.slug,
            },
        )

        return tenant

    def _generate_tenant_slug(self, username: str) -> str:
        """
        根据用户名生成租户 slug

        Args:
            username: 用户名

        Returns:
            str: 租户 slug
        """
        # 转换为小写，替换非法字符
        slug = username.lower()
        slug = re.sub(r"[^a-z0-9-]", "-", slug)
        slug = re.sub(r"-+", "-", slug)  # 多个连字符合并
        slug = slug.strip("-")
        return slug[:50] if len(slug) > 50 else slug