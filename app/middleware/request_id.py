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

# 请求 ID 头名称
REQUEST_ID_HEADER = "X-Request-ID"

class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求 ID 中间件"""
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 获取或生成请求 ID
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())

        # 将请求 ID 存储到 request.state
        request.state.request_id = request_id

        # 处理请求
        response = await call_next(request)

        # 在响应头中返回请求 ID
        response.headers[REQUEST_ID_HEADER] = request_id

        return response


def get_request_id(request: Request)->str:
    return getattr(request.state,"request_id", str(uuid.uuid4()))