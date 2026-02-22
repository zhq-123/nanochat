# app/api/deps.py
"""
API 依赖注入模块

提供常用的依赖注入函数：
- 数据库会话
- 当前用户
- 分页参数
- 等等
"""
from typing import Optional, AsyncGenerator

from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session

from app.core.config import Settings, get_settings


def get_settings_dep() -> Settings:
    """获取配置依赖"""
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话依赖

    用于 FastAPI 路由中注入数据库会话

    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async for session in get_async_session():
        yield session


class PaginationParams:
    """分页参数"""

    def __init__(self,
                 page: int = Query(default=1, ge=1, description="页码"),
                 page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
                 ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


class SortsParams:
    """排序参数"""

    def __init__(self,
                 sort: Optional[str] =
                 Query(default="-created_at", description="排序字段，-前缀表示降序")
                 ):
        self.sort = sort
        if sort:
            self.desc = sort.startswith("-")
            self.field = sort.lstrip("-")
        else:
            self.desc = True
            self.field = "created_at"
