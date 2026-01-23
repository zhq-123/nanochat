# app/schemas/response.py
"""
统一响应模型定义

提供：
- 统一的 API 响应格式
- 分页响应格式
- 泛型响应支持
"""
from typing import TypeVar, Optional, Generic, List

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


class ErrorDetail(BaseModel):
    """错误详情"""

    field: Optional[str] = Field(default=None, description="错误字段")
    message: str = Field(description="错误消息")
    code: Optional[str] = Field(default=None, description="错误码")


class ErrorResponse(ResponseBase):
    """
    错误响应模型

    用于返回错误信息
    """

    data: None = Field(default=None, description="错误响应无数据")
    errors: Optional[List[ErrorDetail]] = Field(
        default=None, description="详细错误列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 100001,
                "message": "Token 已过期",
                "data": None,
                "request_id": "req-xxx-xxx",
                "errors": None,
            }
        }


class PaginationMeta(BaseModel):
    """分页元数据"""

    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total: int = Field(description="总记录数")
    total_pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginatedResponse(ResponseBase, Generic[T]):
    """
    分页响应模型

    用于列表查询的分页返回

    Example:
        PaginatedResponse[UserOut](
            data=users,
            meta=PaginationMeta(...)
        )
    """

    data: List[T] = Field(default_factory=list, description="数据列表")
    meta: PaginationMeta = Field(description="分页信息")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "success",
                "data": [{"id": "xxx", "name": "example"}],
                "meta": {
                    "page": 1,
                    "page_size": 20,
                    "total": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False,
                },
                "request_id": "req-xxx-xxx",
            }
        }


# ==================== 预定义响应类型 ====================
class SuccessResponse(Response[None]):
    """成功响应（无数据）"""

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "操作成功",
                "data": None,
                "request_id": "req-xxx-xxx",
            }
        }


class IdResponse(BaseModel):
    """仅返回 ID 的响应数据"""

    id: str = Field(description="资源 ID")


class MessageResponse(BaseModel):
    """仅返回消息的响应数据"""

    message: str = Field(description="消息内容")