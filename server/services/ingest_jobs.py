"""
异步入库任务体：更新 documents 状态并调用 RagService。
"""

from __future__ import annotations

import os

from flask import current_app

from extensions import db
from models.document import Document
from models.document_status import DocumentStatus
from models.knowledge_base import KnowledgeBase
from services.rag_service import RagService


def run_ingest_for_document(doc_id: int) -> None:
    doc: Document | None = db.session.get(Document, doc_id)
    if not doc or not doc.storage_path:
        return

    kb: KnowledgeBase | None = db.session.get(KnowledgeBase, doc.knowledge_base_id)
    if not kb:
        doc.status = DocumentStatus.FAILED.value
        doc.ingest_error = "知识库不存在"
        db.session.commit()
        return

    upload_dir = current_app.config["UPLOAD_DIR"]
    file_path = os.path.join(upload_dir, doc.storage_path)
    if not os.path.isfile(file_path):
        doc.status = DocumentStatus.FAILED.value
        doc.ingest_error = "文件不存在，可能已被移动或删除"
        db.session.commit()
        return

    doc.status = DocumentStatus.PROCESSING.value
    doc.ingest_error = None
    db.session.commit()

    try:
        RagService.clear_partial_ingest(doc_id=doc_id, collection_name=kb.collection_name)
        RagService.ingest_document(
            doc_id=doc.id,
            file_path=file_path,
            filename=doc.filename,
            title=doc.title,
            collection_name=kb.collection_name,
        )
    except Exception as e:
        try:
            RagService.clear_partial_ingest(doc_id=doc_id, collection_name=kb.collection_name)
        except Exception:
            pass
        doc = db.session.get(Document, doc_id)
        if doc:
            doc.status = DocumentStatus.FAILED.value
            doc.ingest_error = (str(e) or "入库失败")[:2000]
            db.session.commit()
