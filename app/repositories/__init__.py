# app/repositories/__init__.py
"""
仓储模块

导出所有仓储类
"""

from app.repositories.base import BaseRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "TenantRepository",
    "UserRepository",
]