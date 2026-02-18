# app/middleware/logging.py
"""
访问日志中间件

记录每个请求的：
- 请求方法和路径
- 响应状态码
- 处理时间
- 请求 ID
"""
import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id import get_request_id

logger = logging.getLogger(__name__)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """访问日志中间件"""

    # 不记录日志的路径
    SKIP_PATHS = {
        "/health",
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/metrics",
        "/favicon.ico",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过某些路径
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        # 获取请求信息
        request_info = self._get_request_info(request)

        # 处理请求
        response: Response = await call_next(request)

        # 计算处理时间
        process_time = (time.time() - start_time) * 1000  # 毫秒

        # 记录访问日志
        self._log_request(request_info, response, process_time)

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response

    def _get_request_info(self, request: Request) -> dict:
        """获取请求信息"""
        return {
            "method": request.method,
            "path": request.url.path,
            "query_string": str(request.url.query) if request.url.query else "",
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "content_length": request.headers.get("content-length", "0"),
            "content_type": request.headers.get("content-type", ""),
        }

    def _get_client_ip(self, request:Request)->str:
        """获取客户端真实 IP"""
        # 优先从代理头获取
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 如果前面的头都没有，说明请求是直接连接到服务器的（没有代理）
        if request.client:
            return request.client.host

        return "unknown"

    def _log_request(
            self, request_info: dict, response: Response, process_time: float
    ) -> None:
        """记录请求日志"""
        status_code = response.status_code

        # 根据状态码选择日志级别
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        # 构建日志消息
        message = (
            f"{request_info['method']} {request_info['path']} "
            f"- {status_code} - {process_time:.2f}ms"
        )

        logger.log(
            log_level,
            message,
            extra={
                **request_info,
                "status_code": status_code,
                "process_time_ms": round(process_time, 2),
                "response_size": response.headers.get("content-length", "0"),
            },
        )
