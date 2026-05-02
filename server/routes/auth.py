"""
鉴权相关接口。

说明：
- 本项目使用简化版 JWT：后端签名 token，前端在 Authorization 头中携带。
- 密码使用 MD5 存储（按需求）。注意：真实生产环境不建议使用 MD5。
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from services.auth_service import AuthService


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    """
    用户登录。

    入参：
    - username: 用户名
    - password: 明文密码
    """

    ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "unknown").split(",")[0].strip()
    limiter = current_app.extensions.get("login_limiter")
    if limiter is not None and not limiter.allow(ip):
        return jsonify({"ok": False, "message": "登录尝试过于频繁，请稍后再试"}), 429

    payload = request.get_json(silent=True) or {}
    token, user = AuthService.login(payload.get("username"), payload.get("password"))
    return {"ok": True, "data": {"access_token": token, "user": user}}


@auth_bp.get("/me")
def me():
    """
    获取当前登录用户信息。
    """

    user = AuthService.require_user()
    return {"ok": True, "data": user}

