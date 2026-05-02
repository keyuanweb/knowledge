"""
问答日志模型（复杂度适中，便于管理员统计）。
"""

from __future__ import annotations

from extensions import db
from models.base import TimestampMixin


class ChatLog(db.Model, TimestampMixin):
    """
    问答记录。

    sources_json：
    - 记录命中文档片段来源（标题、chunk_index、相似度等），便于复盘。
    """

    __tablename__ = "chat_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False, index=True, comment="用户ID")
    question = db.Column(db.Text, nullable=False, comment="用户问题")
    answer = db.Column(db.Text, nullable=False, comment="模型回答")
    sources_json = db.Column(db.Text, nullable=False, default="[]", comment="来源JSON")

