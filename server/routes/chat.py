"""
问答接口（RAG）。
"""

from __future__ import annotations

import json

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context

from models.chat_log import ChatLog
from services.admin_service import AdminService
from services.auth_service import AuthService
from services.rag_service import RagService


chat_bp = Blueprint("chat", __name__)


@chat_bp.get("/knowledge-bases")
def list_knowledge_bases():
    """
    知识库列表（已登录用户，用于问答与上传选择）。
    """

    AuthService.require_user()
    return {"ok": True, "data": AdminService.list_knowledge_bases()}


@chat_bp.post("/ask")
def ask():
    """
    发起问答（NDJSON 流式）。

    每行一个 JSON 对象：
    - {\"type\":\"meta\",\"sources\":[...]} 首包，含引用来源
    - {\"type\":\"token\",\"text\":\"...\"} 模型增量文本
    - {\"type\":\"done\"} 结束（此时服务端已写入 chat_logs）
    - {\"type\":\"error\",\"message\":\"...\"} 错误

    入参 JSON：
    - question: 用户问题（必填）
    - knowledge_base_id: 知识库 ID（必填）
    """

    user = AuthService.require_user()
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"ok": False, "message": "question 不能为空"}), 400

    max_q = int(current_app.config.get("MAX_QUESTION_LENGTH") or 8000)
    if len(question) > max_q:
        return jsonify({"ok": False, "message": f"问题过长，最多 {max_q} 个字符"}), 400

    kb_raw = payload.get("knowledge_base_id")
    if kb_raw is None or kb_raw == "":
        return jsonify({"ok": False, "message": "请选择知识库 knowledge_base_id"}), 400
    try:
        knowledge_base_id = int(kb_raw)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "knowledge_base_id 无效"}), 400

    uid = user["id"]

    @stream_with_context
    def generate():
        try:
            prompt, sources = RagService.build_rag_prompt_and_sources(question, knowledge_base_id)
            yield (
                json.dumps(
                    {"type": "meta", "sources": [s.__dict__ for s in sources]},
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )
            parts: list[str] = []
            for piece in RagService.stream_llm_answer_chunks(prompt):
                parts.append(piece)
                yield json.dumps({"type": "token", "text": piece}, ensure_ascii=False, default=str) + "\n"
            answer = "".join(parts)
            RagService.save_chat_log(uid, question, answer, sources)
            yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"
        except ValueError as e:
            yield json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps(
                {"type": "error", "message": str(e) or "问答失败"},
                ensure_ascii=False,
            ) + "\n"

    return Response(
        generate(),
        mimetype="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@chat_bp.get("/history")
def history():
    """
    当前用户的问答历史（按时间倒序）。
    """

    user = AuthService.require_user()
    limit = request.args.get("limit", default=50, type=int) or 50
    limit = max(1, min(limit, 200))

    rows = (
        ChatLog.query.filter_by(user_id=user["id"])
        .order_by(ChatLog.id.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in rows:
        try:
            sources = json.loads(r.sources_json or "[]")
        except json.JSONDecodeError:
            sources = []
        out.append(
            {
                "id": r.id,
                "question": r.question,
                "answer": r.answer,
                "sources": sources,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return {"ok": True, "data": out}

