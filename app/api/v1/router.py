# app/api/v1/router.py
"""
API V1 路由汇总

集中管理所有 v1 版本的路由
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, auth

# 创建 v1 路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["健康检查"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"],
)
