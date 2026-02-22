# app/core/security.py
"""
安全工具模块

提供：
- 密码加密与验证
- 安全相关配置
"""
import bcrypt
from passlib.context import CryptContext

# 密码哈希上下文
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # 加密强度，越高越安全但越慢
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed.encode("utf-8"),
    )


def check_password_strength(password: str) -> tuple[bool, str]:
    """
    检查密码强度

    规则：
    - 最少 8 个字符
    - 包含大写字母
    - 包含小写字母
    - 包含数字
    - 包含特殊字符（可选）

    Args:
        password: 密码

    Returns:
        tuple: (是否合格, 错误消息)
    """
    if len(password) < 8:
        return False, "密码长度至少为 8 个字符"

    if not any(c.islower() for c in password):
        return False, "密码必须包含小写字母"

    if not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"

    return True, ""
