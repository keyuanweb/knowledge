"""
用户表模型。
"""

from __future__ import annotations

from extensions import db
from models.base import TimestampMixin


class User(db.Model, TimestampMixin):
    """
    用户实体。

    字段说明：
    - role: admin / user 两类角色
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, comment="用户名")
    password_md5 = db.Column(db.String(32), nullable=False, comment="MD5 密码（按需求）")
    role = db.Column(db.String(16), nullable=False, default="user", comment="角色：admin/user")

