# app/core/error_codes.py
"""
错误码定义模块

错误码格式: XXYYYY
- XX: 模块标识
- YYYY: 具体错误

模块划分:
- 00: 系统级错误
- 10: 认证授权
- 20: 用户相关
- 30: 对话相关
- 40: 知识库相关
- 50: Agent 相关
- 60: 文件存储
- 70: 外部服务
"""
from enum import IntEnum


class ErrorCode(IntEnum):
    """错误码枚举"""

    # ==================== 成功 ====================
    SUCCESS = 0

    # ==================== 系统级错误 (00xxxx) ====================
    SYSTEM_ERROR = 10000  # 系统内部错误
    VALIDATION_ERROR = 10001  # 参数校验错误
    NOT_FOUND = 10002  # 资源不存在
    METHOD_NOT_ALLOWED = 10003  # 请求方法不允许
    RATE_LIMIT_EXCEEDED = 10004  # 请求频率超限
    SERVICE_UNAVAILABLE = 10005  # 服务不可用
    DATABASE_ERROR = 10006  # 数据库错误
    REDIS_ERROR = 10007  # Redis 错误
    TIMEOUT_ERROR = 10008  # 请求超时

    # ==================== 认证授权错误 (10xxxx) ====================
    UNAUTHORIZED = 100001  # 未认证
    TOKEN_EXPIRED = 100002  # Token 过期
    TOKEN_INVALID = 100003  # Token 无效
    REFRESH_TOKEN_EXPIRED = 100004  # Refresh Token 过期
    PERMISSION_DENIED = 100005  # 权限不足
    ACCOUNT_DISABLED = 100006  # 账号已禁用
    ACCOUNT_LOCKED = 100007  # 账号已锁定
    API_KEY_INVALID = 100008  # API Key 无效
    API_KEY_EXPIRED = 100009  # API Key 过期

    # ==================== 用户相关错误 (20xxxx) ====================
    USER_NOT_FOUND = 200001  # 用户不存在
    USER_ALREADY_EXISTS = 200002  # 用户已存在
    PASSWORD_INCORRECT = 200003  # 密码错误
    PASSWORD_TOO_WEAK = 200004  # 密码强度不足
    EMAIL_ALREADY_EXISTS = 200005  # 邮箱已存在
    EMAIL_NOT_VERIFIED = 200006  # 邮箱未验证
    PHONE_ALREADY_EXISTS = 200007  # 手机号已存在
    VERIFICATION_CODE_ERROR = 200008  # 验证码错误
    VERIFICATION_CODE_EXPIRED = 200009  # 验证码过期

    # ==================== 租户相关错误 (21xxxx) ====================
    TENANT_NOT_FOUND = 210001  # 租户不存在
    TENANT_DISABLED = 210002  # 租户已禁用
    TENANT_QUOTA_EXCEEDED = 210003  # 租户配额超限

    # ==================== 对话相关错误 (30xxxx) ====================
    CONVERSATION_NOT_FOUND = 300001  # 对话不存在
    CONVERSATION_LIMIT_EXCEEDED = 300002  # 对话数量超限
    MESSAGE_NOT_FOUND = 300003  # 消息不存在
    MESSAGE_TOO_LONG = 300004  # 消息过长
    CONTEXT_TOO_LONG = 300005  # 上下文过长
    STREAM_INTERRUPTED = 300006  # 流式输出中断

    # ==================== 模型相关错误 (31xxxx) ====================
    MODEL_NOT_FOUND = 310001  # 模型不存在
    MODEL_NOT_AVAILABLE = 310002  # 模型不可用
    MODEL_QUOTA_EXCEEDED = 310003  # 模型配额超限
    MODEL_RATE_LIMITED = 310004  # 模型请求限流
    MODEL_RESPONSE_ERROR = 310005  # 模型响应错误

    # ==================== 知识库相关错误 (40xxxx) ====================
    KNOWLEDGE_BASE_NOT_FOUND = 400001  # 知识库不存在
    KNOWLEDGE_BASE_LIMIT_EXCEEDED = 400002  # 知识库数量超限
    DOCUMENT_NOT_FOUND = 400003  # 文档不存在
    DOCUMENT_PARSE_ERROR = 400004  # 文档解析失败
    DOCUMENT_TOO_LARGE = 400005  # 文档过大
    EMBEDDING_ERROR = 400006  # 向量化失败
    RETRIEVAL_ERROR = 400007  # 检索失败

    # ==================== Agent 相关错误 (50xxxx) ====================
    AGENT_NOT_FOUND = 500001  # Agent 不存在
    AGENT_EXECUTION_ERROR = 500002  # Agent 执行失败
    TOOL_NOT_FOUND = 500003  # 工具不存在
    TOOL_EXECUTION_ERROR = 500004  # 工具执行失败
    WORKFLOW_NOT_FOUND = 500005  # 工作流不存在
    WORKFLOW_EXECUTION_ERROR = 500006  # 工作流执行失败

    # ==================== 文件存储错误 (60xxxx) ====================
    FILE_NOT_FOUND = 600001  # 文件不存在
    FILE_TOO_LARGE = 600002  # 文件过大
    FILE_TYPE_NOT_ALLOWED = 600003  # 文件类型不允许
    FILE_UPLOAD_ERROR = 600004  # 文件上传失败
    STORAGE_ERROR = 600005  # 存储服务错误

    # ==================== 外部服务错误 (70xxxx) ====================
    EXTERNAL_SERVICE_ERROR = 700001  # 外部服务错误
    OPENAI_API_ERROR = 700002  # OpenAI API 错误
    OAUTH_ERROR = 700003  # OAuth 认证错误
    WEBHOOK_ERROR = 700004  # Webhook 调用失败


# 错误码对应的默认消息
ERROR_MESSAGES = {
    # 成功
    ErrorCode.SUCCESS: "操作成功",

    # 系统级错误
    ErrorCode.SYSTEM_ERROR: "系统内部错误，请稍后重试",
    ErrorCode.VALIDATION_ERROR: "参数校验失败",
    ErrorCode.NOT_FOUND: "请求的资源不存在",
    ErrorCode.METHOD_NOT_ALLOWED: "请求方法不允许",
    ErrorCode.RATE_LIMIT_EXCEEDED: "请求频率超限，请稍后重试",
    ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
    ErrorCode.DATABASE_ERROR: "数据库操作失败",
    ErrorCode.REDIS_ERROR: "缓存服务异常",
    ErrorCode.TIMEOUT_ERROR: "请求超时",

    # 认证授权错误
    ErrorCode.UNAUTHORIZED: "请先登录",
    ErrorCode.TOKEN_EXPIRED: "登录已过期，请重新登录",
    ErrorCode.TOKEN_INVALID: "无效的认证信息",
    ErrorCode.REFRESH_TOKEN_EXPIRED: "登录已过期，请重新登录",
    ErrorCode.PERMISSION_DENIED: "权限不足",
    ErrorCode.ACCOUNT_DISABLED: "账号已被禁用",
    ErrorCode.ACCOUNT_LOCKED: "账号已被锁定",
    ErrorCode.API_KEY_INVALID: "无效的 API Key",
    ErrorCode.API_KEY_EXPIRED: "API Key 已过期",

    # 用户相关错误
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.USER_ALREADY_EXISTS: "用户已存在",
    ErrorCode.PASSWORD_INCORRECT: "密码错误",
    ErrorCode.PASSWORD_TOO_WEAK: "密码强度不足",
    ErrorCode.EMAIL_ALREADY_EXISTS: "邮箱已被注册",
    ErrorCode.EMAIL_NOT_VERIFIED: "邮箱尚未验证",
    ErrorCode.PHONE_ALREADY_EXISTS: "手机号已被注册",
    ErrorCode.VERIFICATION_CODE_ERROR: "验证码错误",
    ErrorCode.VERIFICATION_CODE_EXPIRED: "验证码已过期",

    # 租户相关错误
    ErrorCode.TENANT_NOT_FOUND: "租户不存在",
    ErrorCode.TENANT_DISABLED: "租户已被禁用",
    ErrorCode.TENANT_QUOTA_EXCEEDED: "租户配额已用尽",

    # 对话相关错误
    ErrorCode.CONVERSATION_NOT_FOUND: "对话不存在",
    ErrorCode.CONVERSATION_LIMIT_EXCEEDED: "对话数量已达上限",
    ErrorCode.MESSAGE_NOT_FOUND: "消息不存在",
    ErrorCode.MESSAGE_TOO_LONG: "消息内容过长",
    ErrorCode.CONTEXT_TOO_LONG: "上下文长度超限",
    ErrorCode.STREAM_INTERRUPTED: "流式输出中断",

    # 模型相关错误
    ErrorCode.MODEL_NOT_FOUND: "模型不存在",
    ErrorCode.MODEL_NOT_AVAILABLE: "模型暂不可用",
    ErrorCode.MODEL_QUOTA_EXCEEDED: "模型调用配额已用尽",
    ErrorCode.MODEL_RATE_LIMITED: "模型调用频率超限",
    ErrorCode.MODEL_RESPONSE_ERROR: "模型响应异常",

    # 知识库相关错误
    ErrorCode.KNOWLEDGE_BASE_NOT_FOUND: "知识库不存在",
    ErrorCode.KNOWLEDGE_BASE_LIMIT_EXCEEDED: "知识库数量已达上限",
    ErrorCode.DOCUMENT_NOT_FOUND: "文档不存在",
    ErrorCode.DOCUMENT_PARSE_ERROR: "文档解析失败",
    ErrorCode.DOCUMENT_TOO_LARGE: "文档大小超限",
    ErrorCode.EMBEDDING_ERROR: "文档向量化失败",
    ErrorCode.RETRIEVAL_ERROR: "知识检索失败",

    # Agent 相关错误
    ErrorCode.AGENT_NOT_FOUND: "Agent 不存在",
    ErrorCode.AGENT_EXECUTION_ERROR: "Agent 执行失败",
    ErrorCode.TOOL_NOT_FOUND: "工具不存在",
    ErrorCode.TOOL_EXECUTION_ERROR: "工具执行失败",
    ErrorCode.WORKFLOW_NOT_FOUND: "工作流不存在",
    ErrorCode.WORKFLOW_EXECUTION_ERROR: "工作流执行失败",

    # 文件存储错误
    ErrorCode.FILE_NOT_FOUND: "文件不存在",
    ErrorCode.FILE_TOO_LARGE: "文件大小超限",
    ErrorCode.FILE_TYPE_NOT_ALLOWED: "不支持的文件类型",
    ErrorCode.FILE_UPLOAD_ERROR: "文件上传失败",
    ErrorCode.STORAGE_ERROR: "存储服务异常",

    # 外部服务错误
    ErrorCode.EXTERNAL_SERVICE_ERROR: "外部服务调用失败",
    ErrorCode.OPENAI_API_ERROR: "AI 服务暂时不可用",
    ErrorCode.OAUTH_ERROR: "第三方登录失败",
    ErrorCode.WEBHOOK_ERROR: "Webhook 调用失败",
}


def get_error_message(code: ErrorCode) -> str:
    """获取错误码对应的默认消息"""
    return ERROR_MESSAGES.get(code, "未知错误")