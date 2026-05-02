"""
鉴权服务（JWT 简化实现）。
"""

from __future__ import annotations

import time

import jwt
from flask import current_app, request

from extensions import db
from models.user import User
from services.errors import AuthRequiredError, ForbiddenError
from services.utils import md5_password


class AuthService:
    """
    登录与权限校验服务类。
    """

    @staticmethod
    def _encode_token(user: User) -> str:
        """
        生成 JWT Token。
        """

        secret = current_app.config["JWT_SECRET"]
        expire_seconds = int(current_app.config.get("JWT_EXPIRE_SECONDS") or 86400)
        payload = {
            "uid": user.id,
            "role": user.role,
            "exp": int(time.time()) + expire_seconds,
            "iat": int(time.time()),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def _decode_token(token: str) -> dict:
        """
        解码 JWT Token。
        """

        secret = current_app.config["JWT_SECRET"]
        return jwt.decode(token, secret, algorithms=["HS256"])

    @staticmethod
    def login(username: str | None, password: str | None) -> tuple[str, dict]:
        """
        登录校验并返回 token 与用户信息。
        """

        username = (username or "").strip()
        password = password or ""
        if not username or not password:
            raise ValueError("用户名或密码不能为空")

        user: User | None = User.query.filter_by(username=username).first()
        if not user:
            raise ValueError("用户名或密码错误")

        if user.password_md5 != md5_password(password):
            raise ValueError("用户名或密码错误")

        token = AuthService._encode_token(user)
        return token, {"id": user.id, "username": user.username, "role": user.role}

    @staticmethod
    def _get_bearer_token() -> str | None:
        """
        从请求头获取 Bearer Token。
        """

        auth = request.headers.get("Authorization") or ""
        if not auth.startswith("Bearer "):
            return None
        return auth.replace("Bearer ", "", 1).strip()

    @staticmethod
    def require_user() -> dict:
        """
        获取当前用户（未登录则抛异常）。
        """

        token = AuthService._get_bearer_token()
        if not token:
            raise AuthRequiredError("未登录或缺少 token")

        try:
            payload = AuthService._decode_token(token)
        except Exception:
            raise AuthRequiredError("token 无效或已过期")
        uid = payload.get("uid")
        if not uid:
            raise AuthRequiredError("token 无效")

        user: User | None = db.session.get(User, uid)
        if not user:
            raise AuthRequiredError("用户不存在")

        return {"id": user.id, "username": user.username, "role": user.role}

    @staticmethod
    def require_admin() -> dict:
        """
        要求管理员角色。
        """

        user = AuthService.require_user()
        if user["role"] != "admin":
            raise ForbiddenError("无管理员权限")
        return user

