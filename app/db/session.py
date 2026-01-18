# app/db/session.py
"""
数据库会话管理模块

提供:
- 异步数据库引擎
- 会话工厂
- 会话依赖注入
"""
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession

from app.core import settings


def create_engine() -> AsyncEngine:
    """
    创建异步数据库引擎

    Returns:
        AsyncEngine: SQLAlchemy 异步引擎实例
    """
    # 连接池配置
    pool_kwargs = {
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_recycle": settings.DATABASE_POOL_RECYCLE,
        "pool_pre_ping": True,
    }

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        future=True,
        **pool_kwargs,
    )

    return engine


# 创建全局引擎实例
engine = create_engine()

# 创建会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话

    用于 FastAPI 依赖注入

    Yields:
        AsyncSession: 数据库会话
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """初始化数据库连接"""
    # 测试连接
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))


async def close_database() -> None:
    """关闭数据库连接"""
    await engine.dispose()
