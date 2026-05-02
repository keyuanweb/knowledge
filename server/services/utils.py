"""
通用工具函数。
"""

from __future__ import annotations

import hashlib


def md5_text(text: str) -> str:
    """
    计算文本 MD5。
    """

    return hashlib.md5(text.encode("utf-8")).hexdigest()


def md5_password(plain_password: str) -> str:
    """
    对密码做 MD5（按需求）。

    注意：
    - 真实生产环境不建议使用 MD5，建议使用 bcrypt/argon2 等安全哈希方案。
    """

    return md5_text(plain_password or "")

