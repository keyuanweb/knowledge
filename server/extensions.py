"""
Flask 扩展初始化模块。

包含：
- SQLAlchemy：MySQL ORM
- CORS：允许前端跨域调用
"""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_extensions(app: Flask) -> None:
    """
    初始化 Flask 扩展。
    """

    # 数据库
    db.init_app(app)

    # 跨域
    origins = app.config.get("CORS_ORIGINS") or "*"
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=False)

