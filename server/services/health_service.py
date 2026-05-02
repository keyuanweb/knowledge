"""
依赖健康检查：MySQL、Chroma、Ollama。
"""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any

from flask import current_app
from sqlalchemy import text

from extensions import db


def check_mysql() -> dict[str, Any]:
    try:
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        return {"ok": True, "detail": "connected"}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:200]}


def check_ollama() -> dict[str, Any]:
    base = (current_app.config.get("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
    url = f"{base}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return {"ok": False, "detail": f"HTTP {resp.status}"}
        return {"ok": True, "detail": base}
    except urllib.error.URLError as e:
        return {"ok": False, "detail": str(e.reason or e)[:200]}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:200]}


def check_chroma() -> dict[str, Any]:
    try:
        from services.rag_service import RagService

        coll = current_app.config.get("CHROMA_COLLECTION") or "enterprise_qa"
        vs = RagService._get_vector_store(str(coll))
        _ = vs._collection.count()
        return {"ok": True, "detail": current_app.config.get("CHROMA_PERSIST_DIR")}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:200]}


def full_health() -> dict[str, Any]:
    mysql = check_mysql()
    ollama = check_ollama()
    chroma = check_chroma()
    ok = mysql["ok"] and ollama["ok"] and chroma["ok"]
    return {
        "ok": ok,
        "checks": {
            "mysql": mysql,
            "ollama": ollama,
            "chroma": chroma,
        },
    }
