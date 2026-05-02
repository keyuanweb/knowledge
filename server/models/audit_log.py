"""
审计日志模型。
"""

from __future__ import annotations

from extensions import db
from models.base import TimestampMixin


class AuditLog(db.Model, TimestampMixin):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    actor_user_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False)
    detail = db.Column(db.Text, nullable=True)
