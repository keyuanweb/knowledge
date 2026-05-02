"""
管理操作审计（写入 audit_logs）。
"""

from __future__ import annotations

import json
from typing import Any

from extensions import db
from models.audit_log import AuditLog


def write_audit(actor_user_id: int, action: str, detail: dict[str, Any] | None = None) -> None:
    try:
        body = json.dumps(detail, ensure_ascii=False, default=str)[:8000] if detail else None
        db.session.add(AuditLog(actor_user_id=actor_user_id, action=action, detail=body))
        db.session.commit()
    except Exception:
        db.session.rollback()
