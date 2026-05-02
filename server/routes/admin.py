"""
管理员后台接口。
"""

from __future__ import annotations

from flask import Blueprint, request

from services.admin_service import AdminService
from services.auth_service import AuthService


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/audit-logs")
def audit_logs():
    """
    最近管理操作审计（管理员）。
    """

    AuthService.require_admin()
    limit = request.args.get("limit", default=100, type=int) or 100
    return {"ok": True, "data": AdminService.list_audit_logs(limit=limit)}


@admin_bp.get("/stats")
def stats():
    """
    获取后台统计数据（管理员专用）。
    """

    AuthService.require_admin()
    return {"ok": True, "data": AdminService.get_stats()}


@admin_bp.post("/docs/upload")
def upload_doc():
    """
    上传文档并入库（管理员专用）。

    表单字段：
    - file: 文件
    - knowledge_base_id: 知识库 ID（必填）
    - title: 文档标题（可选；不传则使用文件名）
    """

    user = AuthService.require_admin()
    if "file" not in request.files:
        return {"ok": False, "message": "缺少上传文件 file"}, 400

    title = (request.form.get("title") or "").strip()
    kb_id = request.form.get("knowledge_base_id", type=int)
    if not kb_id:
        return {"ok": False, "message": "请选择知识库 knowledge_base_id"}, 400

    f = request.files["file"]
    result = AdminService.upload_and_enqueue_ingest(
        file_storage=f,
        title=title,
        created_by=user["id"],
        knowledge_base_id=kb_id,
    )
    return {"ok": True, "data": result}


@admin_bp.get("/docs")
def list_docs():
    """
    获取文档列表（管理员专用）。
    """

    AuthService.require_admin()
    return {"ok": True, "data": AdminService.list_documents()}


@admin_bp.delete("/docs/<int:doc_id>")
def delete_doc(doc_id: int):
    """
    删除文档（管理员）。
    """

    user = AuthService.require_admin()
    data = AdminService.delete_document(doc_id, actor_id=user["id"])
    return {"ok": True, "data": data}


@admin_bp.post("/docs/<int:doc_id>/reindex")
def reindex_doc(doc_id: int):
    """
    对已上传文件的文档重新向量化（管理员）。
    """

    user = AuthService.require_admin()
    data = AdminService.reindex_document(doc_id=doc_id, actor_id=user["id"])
    return {"ok": True, "data": data}


@admin_bp.get("/knowledge-bases")
def list_knowledge_bases():
    """
    知识库列表（管理员）。
    """

    AuthService.require_admin()
    return {"ok": True, "data": AdminService.list_knowledge_bases()}


@admin_bp.post("/knowledge-bases")
def create_knowledge_base():
    """
    新建知识库（管理员）。
    """

    actor = AuthService.require_admin()
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    description = (body.get("description") or "").strip()
    data = AdminService.create_knowledge_base(name=name, description=description, actor_id=actor["id"])
    return {"ok": True, "data": data}


@admin_bp.delete("/knowledge-bases/<int:kb_id>")
def delete_knowledge_base(kb_id: int):
    """
    删除知识库（管理员）：存在关联文档时拒绝。
    """

    actor = AuthService.require_admin()
    data = AdminService.delete_knowledge_base(kb_id, actor_id=actor["id"])
    return {"ok": True, "data": data}


@admin_bp.get("/users")
def list_users():
    """
    获取用户列表（管理员专用）。
    """

    AuthService.require_admin()
    return {"ok": True, "data": AdminService.list_users()}


@admin_bp.post("/users")
def create_user():
    """
    新建用户（管理员）：JSON username、password、role（可选，默认 user）。
    """

    actor = AuthService.require_admin()
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")
    role = body.get("role") or "user"
    data = AdminService.create_user(username=username, password=password, role=role, actor_id=actor["id"])
    return {"ok": True, "data": data}


@admin_bp.patch("/users/<int:user_id>")
def patch_user(user_id: int):
    """
    更新用户（管理员）：JSON 可含 username、role、password（非空则重置密码）。
    """

    actor = AuthService.require_admin()
    body = request.get_json(silent=True) or {}
    data = AdminService.update_user(user_id=user_id, actor_id=actor["id"], payload=body)
    return {"ok": True, "data": data}


@admin_bp.delete("/users/<int:user_id>")
def delete_user(user_id: int):
    """
    删除用户（管理员）。
    """

    actor = AuthService.require_admin()
    data = AdminService.delete_user(target_id=user_id, actor_id=actor["id"])
    return {"ok": True, "data": data}

