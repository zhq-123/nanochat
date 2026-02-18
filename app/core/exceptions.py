# app/core/exceptions.py
"""
自定义异常类模块

定义项目中使用的所有自定义异常：
- BusinessException: 业务异常基类
- AuthException: 认证相关异常
- ValidationException: 参数校验异常
- NotFoundException: 资源不存在异常
- 等等
"""
from typing import Optional, Any, List, Dict

from app.core.error_codes import ErrorCode, get_error_message


class BusinessException(Exception):
    """
    业务异常基类

    所有业务相关的异常都应该继承此类

    Attributes:
        code: 错误码
        message: 错误消息
        data: 额外数据
        errors: 详细错误列表
    """

    def __init__(self,
                 code: ErrorCode = ErrorCode.SYSTEM_ERROR,
                 message: Optional[str] = None,
                 data: Any = None,
                 errors: Optional[List[Dict[str, Any]]] = None,
                 ):
        self.code = code
        self.message = message or get_error_message(code)
        self.data = data
        self.errors = errors
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }
        if self.errors:
            result["errors"] = self.errors
        return result


class AuthenticationException(BusinessException):
    """认证异常"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.UNAUTHORIZED,
        message: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(code=code, message=message, **kwargs)


class AuthorizationException(BusinessException):
    """授权异常"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.PERMISSION_DENIED,
        message: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(code=code, message=message, **kwargs)


class ValidationException(BusinessException):
    """参数校验异常"""

    def __init__(
        self,
        message: str = "参数校验失败",
        errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            errors=errors,
            **kwargs,
        )


class NotFoundException(BusinessException):
    """资源不存在异常"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.NOT_FOUND,
        message: Optional[str] = None,
        resource: Optional[str] = None,
        **kwargs,
    ):
        if message is None and resource:
            message = f"{resource}不存在"
        super().__init__(code=code, message=message, **kwargs)


class ConflictException(BusinessException):
    """资源冲突异常（如重复创建）"""

    def __init__(
        self,
        message: str = "资源已存在",
        **kwargs,
    ):
        super().__init__(
            code=ErrorCode.USER_ALREADY_EXISTS,
            message=message,
            **kwargs,
        )


class RateLimitException(BusinessException):
    """限流异常"""

    def __init__(
        self,
        message: str = "请求频率超限，请稍后重试",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        data = {"retry_after": retry_after} if retry_after else None
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            data=data,
            **kwargs,
        )


class ExternalServiceException(BusinessException):
    """外部服务异常"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        message: Optional[str] = None,
        service_name: Optional[str] = None,
        **kwargs,
    ):
        if message is None and service_name:
            message = f"{service_name}服务暂时不可用"
        super().__init__(code=code, message=message, **kwargs)


class DatabaseException(BusinessException):
    """数据库异常"""

    def __init__(
        self,
        message: str = "数据库操作失败",
        **kwargs,
    ):
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            **kwargs,
        )


class FileException(BusinessException):
    """文件操作异常"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.FILE_UPLOAD_ERROR,
        message: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(code=code, message=message, **kwargs)


class ModelException(BusinessException):
    """AI 模型相关异常"""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.MODEL_RESPONSE_ERROR,
        message: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs,
    ):
        if message is None and model_name:
            message = f"模型 {model_name} 响应异常"
        super().__init__(code=code, message=message, **kwargs)