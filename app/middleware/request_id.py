# app/middleware/request_id.py
"""
请求 ID 中间件

为每个请求生成唯一 ID，用于：
- 日志追踪
- 错误排查
- 分布式追踪
"""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.log_config import request_id_var

# 请求 ID 头名称
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求 ID 中间件

    执行顺序：
    1. 从请求头获取或生成 request_id
    2. 存储到 request.state
    3. 注入到日志上下文变量
    4. 添加到响应头
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 获取或生成请求 ID
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())

        # 将请求 ID 存储到 request.state
        request.state.request_id = request_id

        token = request_id_var.set(request_id)

        try:
            # 处理请求
            response = await call_next(request)

            # 在响应头中返回请求 ID
            response.headers[REQUEST_ID_HEADER] = request_id

            return response
        finally:
            request_id_var.reset(token)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))
