# app/core/logging.py
"""
日志配置模块

支持两种日志格式：
- JSON 格式：适合生产环境，便于日志收集和分析
- TEXT 格式：适合开发环境，便于阅读
- 请求 ID 追踪
- 结构化上下文信息
"""
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any, Dict, Optional

from app.core.config import settings


request_id_var:ContextVar[Optional[str]] = ContextVar("request_id",  default=None)


class RequestIdFilter(logging.Filter):
    """
    日志过滤器：添加 request_id 到日志记录
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True

class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # 添加 extra 字段
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "request_id"
            ]:
                log_data[key] = value

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """文本格式日志格式化器"""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

def setup_logging() -> None:
    """配置日志系统"""
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # 移除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # 添加请求 ID 过滤器
    console_handler.addFilter(RequestIdFilter())

    # 根据配置选择格式化器
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 设置第三方库日志级别
    _configure_third_party_loggers()

    # 记录日志系统初始化
    logging.info(
        "Logging system initialized",
        extra={
            "log_level": settings.LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
        },
    )


def _configure_third_party_loggers() -> None:
    """配置第三方库的日志级别"""
    # uvicorn
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # SQLAlchemy
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DATABASE_ECHO else logging.WARNING
    )
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # 消息队列
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)

    # HTTP 客户端
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # 其他
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
