# app/utils/response.py
"""
响应工具函数

提供便捷的响应构造方法
"""
from typing import TypeVar, Optional, Any, List

from starlette.requests import Request

from app.core.error_codes import ErrorCode, get_error_message
from app.schemas.response import Response, ErrorResponse, ErrorDetail, PaginatedResponse, \
    PaginationMeta

T = TypeVar("T")


def get_request_id(request: Optional[Request] = None) -> Optional[str]:
    """从请求中获取 request_id"""
    if request and hasattr(request.state, "request_id"):
        return request.state.request_id
    return None


def success_response(
        data: Any = None,
        message: str = "success",
        request: Optional[Request] = None,
) -> Response:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 成功消息
        request: FastAPI 请求对象

    Returns:
        Response: 统一响应对象
    """
    return Response(
        code=ErrorCode.SUCCESS,
        message=message,
        data=data,
        request_id=get_request_id(request),
    )


def error_response(
        code: ErrorCode,
        message: Optional[str] = None,
        errors: Optional[List[ErrorDetail]] = None,
        request: Optional[Request] = None,
) -> ErrorResponse:
    """
    创建错误响应

    Args:
        code: 错误码
        message: 错误消息（可选，默认使用错误码对应消息）
        errors: 详细错误列表
        request: FastAPI 请求对象

    Returns:
        ErrorResponse: 错误响应对象
    """
    return ErrorResponse(
        code=code,
        message=message or get_error_message(code),
        errors=errors,
        request_id=get_request_id(request),
    )


def paginated_response(
        data: List[T],
        total: int,
        page: int,
        page_size: int,
        message: str = "success",
        request: Optional[Request] = None,
) -> PaginatedResponse[T]:
    """
    创建分页响应

    Args:
        data: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页数量
        message: 成功消息
        request: FastAPI 请求对象

    Returns:
        PaginatedResponse: 分页响应对象
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return PaginatedResponse(
        code=ErrorCode.SUCCESS,
        message=message,
        data=data,
        meta=meta,
        request_id=get_request_id(request),
    )
