"""
知识库：对应独立 Chroma collection，文档归属某一知识库。
"""

from __future__ import annotations

from extensions import db
from models.base import TimestampMixin


class KnowledgeBase(db.Model, TimestampMixin):
    """
    知识库实体。

    collection_name:
    - 与 Chroma 持久化目录下的 collection 一一对应；
    - 预置「默认知识库」使用与配置一致的 enterprise_qa，兼容已有向量数据。
    """

    __tablename__ = "knowledge_bases"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False, comment="展示名称")
    description = db.Column(db.String(512), nullable=False, default="", comment="说明")
    collection_name = db.Column(db.String(128), nullable=False, unique=True, comment="Chroma collection 名")
