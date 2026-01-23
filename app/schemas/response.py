# app/schemas/response.py
"""
统一响应模型定义

提供：
- 统一的 API 响应格式
- 分页响应格式
- 泛型响应支持
"""
from typing import TypeVar, Optional, Generic

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class ResponseBase(BaseModel):
    """响应基类"""

    code: int = Field(default=0, description="业务状态码，0 表示成功")
    message: str = Field(default="success", description="状态消息")
    request_id: Optional[str] = Field(default=None, description="请求追踪 ID")


class Response(ResponseBase, Generic[T]):
    """
    统一响应模型

    泛型类，支持任意类型的 data 字段

    Example:
        Response[UserOut](data=user)
        Response[List[UserOut]](data=users)
    """

    data: Optional[T] = Field(default=None, description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "success",
                "data": {"id": "xxx", "name": "example"},
                "request_id": "req-xxx-xxx",
            }
        }