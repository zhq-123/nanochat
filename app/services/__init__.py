# app/services/__init__.py
"""
服务模块

导出所有服务类
"""

from app.services.user_service import UserService

__all__ = [
    "UserService",
]