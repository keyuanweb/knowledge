"""
模型公共基类。
"""

from __future__ import annotations

from datetime import datetime

from extensions import db


class TimestampMixin:
    """
    时间戳混入类。

    用途：
    - 为表提供 created_at 字段，便于统计与审计。
    """

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

