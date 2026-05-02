"""
文档与切片模型。
"""

from __future__ import annotations

from extensions import db
from models.base import TimestampMixin
from models.document_status import DocumentStatus


class Document(db.Model, TimestampMixin):
    """
    文档表。

    status 存枚举值（DocumentStatus.value），中文展示见 status_label_zh。
    """

    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    knowledge_base_id = db.Column(
        db.Integer,
        db.ForeignKey("knowledge_bases.id"),
        nullable=False,
        index=True,
        comment="所属知识库",
    )
    title = db.Column(db.String(255), nullable=False, comment="文档标题")
    filename = db.Column(db.String(255), nullable=False, comment="原始文件名")
    file_type = db.Column(db.String(32), nullable=False, comment="文件类型，如 pdf/docx/md/txt")
    storage_path = db.Column(db.String(512), nullable=False, default="", comment="相对 uploads 的存储文件名")
    status = db.Column(
        db.String(16),
        nullable=False,
        default=DocumentStatus.PENDING.value,
        comment="状态：pending/processing/indexed/failed（见 DocumentStatus）",
    )
    ingest_error = db.Column(db.Text, nullable=True, comment="入库失败原因")
    created_by = db.Column(db.Integer, nullable=False, comment="创建者用户ID")


class DocChunk(db.Model, TimestampMixin):
    """
    文档切片表（用于审计与统计；真实检索以向量库为准）。
    """

    __tablename__ = "doc_chunks"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    doc_id = db.Column(db.Integer, nullable=False, index=True, comment="文档ID")
    chunk_index = db.Column(db.Integer, nullable=False, comment="切片序号")
    content = db.Column(db.Text, nullable=False, comment="切片文本内容")
    content_md5 = db.Column(db.String(32), nullable=False, comment="切片内容MD5（用于去重）")

