"""
管理员后台业务逻辑。
"""

from __future__ import annotations

import os
import uuid

from flask import current_app
from werkzeug.datastructures import FileStorage

from sqlalchemy import func

from extensions import db
from models.chat_log import ChatLog
from models.document import DocChunk, Document
from models.document_status import DocumentStatus, status_label_zh
from models.knowledge_base import KnowledgeBase
from models.user import User
from services.audit_service import write_audit
from services.file_loader import FileLoader
from services.ingest_queue import submit_document_ingest
from services.rag_service import RagService
from services.utils import md5_password


class AdminService:
    """
    管理员相关服务类。
    """

    @staticmethod
    def list_audit_logs(limit: int = 200) -> list[dict]:
        """
        最近审计记录（管理员查看）。
        """

        from models.audit_log import AuditLog

        lim = max(1, min(500, int(limit)))
        rows = AuditLog.query.order_by(AuditLog.id.desc()).limit(lim).all()
        return [
            {
                "id": r.id,
                "actor_user_id": r.actor_user_id,
                "action": r.action,
                "detail": r.detail,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    @staticmethod
    def get_stats() -> dict:
        """
        获取统计数据（用于后台 Home 图表/卡片）。
        """

        user_count = db.session.query(User).count()
        doc_count = db.session.query(Document).count()
        chunk_count = db.session.query(DocChunk).count()
        chat_count = db.session.query(ChatLog).count()
        kb_count = db.session.query(KnowledgeBase).count()

        return {
            "user_count": user_count,
            "doc_count": doc_count,
            "chunk_count": chunk_count,
            "chat_count": chat_count,
            "kb_count": kb_count,
        }

    @staticmethod
    def list_users() -> list[dict]:
        """
        用户列表（不含密码）。
        """

        users = User.query.order_by(User.id.asc()).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]

    @staticmethod
    def update_user(user_id: int, actor_id: int, payload: dict) -> dict:
        """
        更新用户：用户名、角色、密码（密码留空则不修改）。
        """

        user: User | None = db.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        if "username" in payload:
            un = (payload.get("username") or "").strip()
            if not un:
                raise ValueError("用户名不能为空")
            existing = User.query.filter(User.username == un, User.id != user_id).first()
            if existing:
                raise ValueError("用户名已存在")
            user.username = un

        if "role" in payload:
            role = (payload.get("role") or "").strip()
            if role not in ("admin", "user"):
                raise ValueError("角色必须为 admin 或 user")
            if user.role == "admin" and role == "user":
                other_admins = User.query.filter(User.role == "admin", User.id != user_id).count()
                if other_admins < 1:
                    raise ValueError("至少需要保留一名其他管理员，无法将该用户改为普通用户")
            user.role = role

        if "password" in payload:
            pwd = payload.get("password")
            if pwd is not None and str(pwd).strip() != "":
                user.password_md5 = md5_password(str(pwd))

        db.session.commit()
        write_audit(actor_user_id=actor_id, action="user.update", detail={"target_id": user_id, "username": user.username})
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    @staticmethod
    def delete_user(target_id: int, actor_id: int) -> dict:
        """
        删除用户：不可删自己、不可删唯一管理员。
        """

        if target_id == actor_id:
            raise ValueError("不能删除当前登录账号")

        user: User | None = db.session.get(User, target_id)
        if not user:
            raise ValueError("用户不存在")

        if user.role == "admin":
            admin_n = User.query.filter_by(role="admin").count()
            if admin_n <= 1:
                raise ValueError("不能删除系统唯一的管理员账号")

        db.session.delete(user)
        db.session.commit()
        write_audit(actor_user_id=actor_id, action="user.delete", detail={"target_id": target_id})
        return {"id": target_id}

    @staticmethod
    def list_documents() -> list[dict]:
        """
        返回文档列表。
        """

        docs = (
            db.session.query(Document, KnowledgeBase.name.label("knowledge_base_name"))
            .join(KnowledgeBase, Document.knowledge_base_id == KnowledgeBase.id)
            .order_by(Document.id.desc())
            .all()
        )
        out = []
        for d, kb_name in docs:
            out.append(
                {
                    "id": d.id,
                    "knowledge_base_id": d.knowledge_base_id,
                    "knowledge_base_name": kb_name,
                    "title": d.title,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "can_reindex": bool(getattr(d, "storage_path", None))
                    and d.status
                    in (
                        DocumentStatus.FAILED.value,
                        DocumentStatus.INDEXED.value,
                        DocumentStatus.UPLOADED.value,
                    ),
                    "status": d.status,
                    "status_label": status_label_zh(d.status),
                    "ingest_error": (d.ingest_error or "")[:500] if getattr(d, "ingest_error", None) else None,
                    "created_by": d.created_by,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
            )
        return out

    @staticmethod
    def list_knowledge_bases() -> list[dict]:
        """
        知识库列表（含文档数量）。
        """

        cnt = (
            db.session.query(Document.knowledge_base_id, func.count(Document.id))
            .group_by(Document.knowledge_base_id)
            .all()
        )
        doc_counts = {kb_id: n for kb_id, n in cnt}
        rows = KnowledgeBase.query.order_by(KnowledgeBase.id.asc()).all()
        return [
            {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description or "",
                "collection_name": kb.collection_name,
                "doc_count": int(doc_counts.get(kb.id, 0)),
                "created_at": kb.created_at.isoformat() if kb.created_at else None,
            }
            for kb in rows
        ]

    @staticmethod
    def create_knowledge_base(name: str, description: str, actor_id: int) -> dict:
        """
        新建知识库：分配独立 Chroma collection（kb_<id>）。
        """

        import uuid

        name = (name or "").strip()
        if not name:
            raise ValueError("知识库名称不能为空")
        desc = (description or "").strip()[:512]
        pending = f"pending_{uuid.uuid4().hex[:20]}"
        kb = KnowledgeBase(name=name, description=desc, collection_name=pending)
        db.session.add(kb)
        db.session.flush()
        kb.collection_name = f"kb_{kb.id}"
        db.session.commit()
        write_audit(actor_user_id=actor_id, action="kb.create", detail={"id": kb.id, "name": kb.name})
        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "collection_name": kb.collection_name,
        }

    @staticmethod
    def upload_and_enqueue_ingest(
        file_storage: FileStorage,
        title: str,
        created_by: int,
        knowledge_base_id: int,
    ) -> dict:
        """
        上传文档并异步入库（立即返回 pending，由后台线程完成向量化）。
        """

        upload_dir = current_app.config["UPLOAD_DIR"]
        os.makedirs(upload_dir, exist_ok=True)

        kb = db.session.get(KnowledgeBase, knowledge_base_id)
        if not kb:
            raise ValueError("知识库不存在")

        filename = file_storage.filename or f"upload-{uuid.uuid4().hex}"
        file_type = FileLoader.detect_type(filename)
        if file_type not in ("txt", "md", "pdf", "docx"):
            raise ValueError("仅支持 txt/md/pdf/docx 文件")

        safe_name = f"{uuid.uuid4().hex}-{filename}"
        file_path = os.path.join(upload_dir, safe_name)
        file_storage.save(file_path)

        doc_title = title or filename
        doc = Document(
            title=doc_title,
            filename=filename,
            file_type=file_type,
            storage_path=safe_name,
            status=DocumentStatus.PENDING.value,
            ingest_error=None,
            created_by=created_by,
            knowledge_base_id=knowledge_base_id,
        )
        db.session.add(doc)
        db.session.commit()

        write_audit(actor_user_id=created_by, action="doc.upload", detail={"doc_id": doc.id, "kb_id": knowledge_base_id})
        submit_document_ingest(current_app._get_current_object(), doc.id)
        return {
            "document": {
                "id": doc.id,
                "title": doc_title,
                "status": DocumentStatus.PENDING.value,
                "status_label": status_label_zh(DocumentStatus.PENDING.value),
                "message": "已接收文件，正在后台入库，请稍后刷新列表查看状态",
            }
        }

    @staticmethod
    def reindex_document(doc_id: int, actor_id: int) -> dict:
        """
        对已存在文件的文档重新执行向量化（需有 storage_path）。
        """

        doc: Document | None = db.session.get(Document, doc_id)
        if not doc:
            raise ValueError("文档不存在")
        if not doc.storage_path:
            raise ValueError("该文档无本地存储记录，无法重建索引，请重新上传")
        if doc.status == DocumentStatus.PROCESSING.value:
            raise ValueError("文档正在入库中，请稍后再试")

        doc.status = DocumentStatus.PENDING.value
        doc.ingest_error = None
        db.session.commit()
        write_audit(actor_user_id=actor_id, action="doc.reindex", detail={"doc_id": doc_id})
        submit_document_ingest(current_app._get_current_object(), doc.id)
        return {
            "id": doc_id,
            "status": DocumentStatus.PENDING.value,
            "status_label": status_label_zh(DocumentStatus.PENDING.value),
        }

    @staticmethod
    def delete_document(doc_id: int, actor_id: int) -> dict:
        """
        删除文档：移除 Chroma 向量、doc_chunks 与 documents 记录。
        """

        doc: Document | None = db.session.get(Document, doc_id)
        if not doc:
            raise ValueError("文档不存在")

        kb: KnowledgeBase | None = db.session.get(KnowledgeBase, doc.knowledge_base_id)
        if not kb:
            raise ValueError("知识库不存在")

        upload_dir = current_app.config["UPLOAD_DIR"]
        if doc.storage_path:
            fp = os.path.join(upload_dir, doc.storage_path)
            if os.path.isfile(fp):
                try:
                    os.remove(fp)
                except OSError:
                    pass

        RagService.delete_document_embeddings(doc_id=doc_id, collection_name=kb.collection_name)
        db.session.delete(doc)
        db.session.commit()
        write_audit(actor_user_id=actor_id, action="doc.delete", detail={"doc_id": doc_id})
        return {"id": doc_id}

    @staticmethod
    def delete_knowledge_base(kb_id: int, actor_id: int) -> dict:
        """
        删除知识库：无关联文档时删除 Chroma collection 与库表记录。

        id=1 为预置默认库，禁止删除。
        """

        if kb_id == 1:
            raise ValueError("系统默认知识库不可删除")

        kb: KnowledgeBase | None = db.session.get(KnowledgeBase, kb_id)
        if not kb:
            raise ValueError("知识库不存在")

        doc_n = Document.query.filter_by(knowledge_base_id=kb_id).count()
        if doc_n > 0:
            raise ValueError(f"该知识库下仍有 {doc_n} 个文档，请先在文档管理中删除全部文档后再删除知识库")

        RagService.delete_chroma_collection(kb.collection_name)
        db.session.delete(kb)
        db.session.commit()
        write_audit(actor_user_id=actor_id, action="kb.delete", detail={"kb_id": kb_id})
        return {"id": kb_id}

