# app/main.py
"""
nanochat 应用入口

FastAPI 应用初始化和配置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.events import lifespan
from app.core.logging import setup_logging
from app.middleware import AccessLogMiddleware, RequestIDMiddleware

# 配置日志
setup_logging()


def create_application() -> FastAPI:
    """
    创建 FastAPI 应用实例

    Returns:
        FastAPI: 配置完成的应用实例
    """
    # 创建 FastAPI 实例
    app = FastAPI(
        **settings.fastapi_kwargs,
        lifespan=lifespan,
    )

    # ==================== 注册中间件 ====================
    # 注意：中间件的注册顺序很重要，后注册的先执行

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # 访问日志中间件
    app.add_middleware(AccessLogMiddleware)

    # 请求 ID 中间件
    app.add_middleware(RequestIDMiddleware)

    # ==================== 注册路由 ====================

    # API v1 路由
    app.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX,
    )

    # 根路由
    @app.get("/", tags=["根路径"])
    async def root():
        """根路径，返回应用信息"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION,
            "docs": settings.DOCS_URL if not settings.is_production else None,
        }

    return app


# 创建应用实例
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )