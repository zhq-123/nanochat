# app/middleware/exception_handler.py
"""
全局异常处理器

捕获并处理所有异常，返回统一格式的错误响应
"""
import logging
import traceback

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import BusinessException, ErrorCode
from app.schemas import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    """获取请求 ID"""
    return getattr(request.state, "request_id", "unknown")


async def business_exception_handler(
        request: Request, exc: BusinessException
) -> JSONResponse:
    """
    业务异常处理器

    处理所有 BusinessException 及其子类
    """
    request_id = get_request_id(request)

    # 记录错误日志
    logger.warning(
        "Business exception occurred",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "error_message": exc.message,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # 构建错误详情
    errors = None
    if exc.errors:
        errors = [
            ErrorDetail(
                field=e.get("field"),
                message=e.get("message", ""),
                code=e.get("code"),
            )
            for e in exc.errors
        ]

    response = ErrorResponse(code=exc.code, message=exc.message,
                             errors=errors, request_id=request_id, )

    # 根据错误类型确定 HTTP 状态码
    status_code = _get_http_status_code(exc.code)

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )


async def validation_exception_handler(
        request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
      请求参数校验异常处理器

      处理 Pydantic 校验失败的情况
      """
    request_id = get_request_id(request)

    # 解析校验错误
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # 跳过 body/query 等前缀
        errors.append(
            ErrorDetail(
                field=field or None,
                message=error["msg"],
                code=error["type"],
            )
        )

    # 记录错误日志
    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "errors": [e.model_dump() for e in errors],
        },
    )

    response = ErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message="参数校验失败",
        errors=errors,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(),
    )


async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    HTTP 异常处理器

    处理 FastAPI/Starlette 的 HTTP 异常
    """
    request_id = get_request_id(request)

    # 映射 HTTP 状态码到错误码
    error_code = _http_status_to_error_code(exc.status_code)

    logger.warning(
        "HTTP exception",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )

    response = ErrorResponse(
        code=error_code,
        message=str(exc.detail) if exc.detail else "请求处理失败",
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )


async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    数据库异常处理器

    处理 SQLAlchemy 相关异常
    """
    request_id = get_request_id(request)

    # 记录详细错误
    logger.error(
        "Database error",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    response = ErrorResponse(
        code=ErrorCode.DATABASE_ERROR,
        message="数据库操作失败，请稍后重试",
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )


async def global_exception_handler(
        request: Request, exc: Exception
) -> JSONResponse:
    """
    全局异常处理器

    处理所有未被捕获的异常
    """
    request_id = get_request_id(request)

    # 记录完整堆栈
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )

    response = ErrorResponse(
        code=ErrorCode.SYSTEM_ERROR,
        message="系统内部错误，请稍后重试",
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )


def register_exception_handler(app: FastAPI):
    """
    注册所有异常处理器

    Args:
        app: FastAPI 应用实例
    """
    # 业务异常
    app.add_exception_handler(BusinessException, business_exception_handler)

    # 参数校验异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # HTTP 异常
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # 数据库异常
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # 全局异常（兜底）
    app.add_exception_handler(Exception, global_exception_handler)


def _get_http_status_code(error_code: ErrorCode) -> int:
    """根据错误码获取 HTTP 状态码"""
    # 认证相关
    if error_code in (
            ErrorCode.UNAUTHORIZED,
            ErrorCode.TOKEN_EXPIRED,
            ErrorCode.TOKEN_INVALID,
            ErrorCode.REFRESH_TOKEN_EXPIRED,
    ):
        return status.HTTP_401_UNAUTHORIZED

    # 授权相关
    if error_code in (
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.ACCOUNT_DISABLED,
            ErrorCode.ACCOUNT_LOCKED,
    ):
        return status.HTTP_403_FORBIDDEN

    # 资源不存在
    if error_code in (
            ErrorCode.NOT_FOUND,
            ErrorCode.USER_NOT_FOUND,
            ErrorCode.CONVERSATION_NOT_FOUND,
            ErrorCode.MESSAGE_NOT_FOUND,
            ErrorCode.KNOWLEDGE_BASE_NOT_FOUND,
            ErrorCode.DOCUMENT_NOT_FOUND,
            ErrorCode.AGENT_NOT_FOUND,
            ErrorCode.TOOL_NOT_FOUND,
            ErrorCode.WORKFLOW_NOT_FOUND,
            ErrorCode.FILE_NOT_FOUND,
            ErrorCode.MODEL_NOT_FOUND,
    ):
        return status.HTTP_404_NOT_FOUND

    # 参数错误
    if error_code == ErrorCode.VALIDATION_ERROR:
        return status.HTTP_422_UNPROCESSABLE_ENTITY

    # 限流
    if error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
        return status.HTTP_429_TOO_MANY_REQUESTS

    # 资源冲突
    if error_code in (
            ErrorCode.USER_ALREADY_EXISTS,
            ErrorCode.EMAIL_ALREADY_EXISTS,
            ErrorCode.PHONE_ALREADY_EXISTS,
    ):
        return status.HTTP_409_CONFLICT

    # 服务不可用
    if error_code == ErrorCode.SERVICE_UNAVAILABLE:
        return status.HTTP_503_SERVICE_UNAVAILABLE

    # 默认返回 400
    return status.HTTP_400_BAD_REQUEST


def _http_status_to_error_code(status_code: int) -> ErrorCode:
    """HTTP 状态码映射到错误码"""
    mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        409: ErrorCode.USER_ALREADY_EXISTS,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.SYSTEM_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
        504: ErrorCode.TIMEOUT_ERROR,
    }
    return mapping.get(status_code, ErrorCode.SYSTEM_ERROR)
