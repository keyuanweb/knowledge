"""
自定义异常类型。

说明：
- 用不同异常类型区分 401/403 等常见鉴权错误，便于前端做正确提示。
"""


class AuthRequiredError(PermissionError):
    """需要登录（401）。"""


class ForbiddenError(PermissionError):
    """权限不足（403）。"""

