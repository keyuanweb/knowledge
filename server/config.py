"""
配置加载模块。

说明：
- 为了便于本地运行，使用环境变量 + 默认值的方式加载配置。
- 生产环境请通过环境变量注入敏感信息（如数据库密码、JWT 密钥）。
"""

from __future__ import annotations

import os


def _env(key: str, default: str | None = None) -> str | None:
    """读取环境变量（不存在则返回默认值）。"""

    value = os.getenv(key)
    return value if value is not None and value != "" else default


def load_config() -> dict:
    """
    加载 Flask 配置字典。

    关键配置：
    - MySQL：连接 db_enterprise_qa（端口 3308）
    - JWT：用于登录鉴权
    - Ollama：大模型与嵌入模型调用
    - Chroma：向量库持久化路径
    """

    mysql_host = _env("MYSQL_HOST", "127.0.0.1")
    mysql_port = _env("MYSQL_PORT", "3306")
    mysql_user = _env("MYSQL_USER", "root")
    mysql_password = _env("MYSQL_PASSWORD", "123456")
    mysql_db = _env("MYSQL_DB", "db_enterprise_qa")

    # SQLAlchemy 连接串（mysql8）
    db_uri = (
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
        "?charset=utf8mb4"
    )

    def _int(key: str, default: int) -> int:
        raw = _env(key, str(default))
        try:
            return int(raw or default)
        except (TypeError, ValueError):
            return default

    def _float_opt(key: str) -> float | None:
        raw = _env(key)
        if raw is None or raw == "":
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    return {
        # Flask
        "DEBUG": _env("FLASK_DEBUG", "1") == "1",
        "HOST": _env("FLASK_HOST", "0.0.0.0"),
        "PORT": int(_env("FLASK_PORT", "5000") or "5000"),
        "SECRET_KEY": _env("SECRET_KEY", "dev-secret-key"),
        "MAX_CONTENT_LENGTH": _int("MAX_UPLOAD_BYTES", 52_428_800),  # 默认 50MB
        # DB
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        # JWT
        "JWT_SECRET": _env("JWT_SECRET", "dev-jwt-secret"),
        "JWT_EXPIRE_SECONDS": int(_env("JWT_EXPIRE_SECONDS", "86400") or "86400"),
        # CORS
        "CORS_ORIGINS": _env("CORS_ORIGINS", "http://localhost:5173"),
        # Ollama
        "OLLAMA_BASE_URL": _env("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_LLM_MODEL": _env("OLLAMA_LLM_MODEL", "qwen3:8b"),
        "OLLAMA_EMBED_MODEL": _env("OLLAMA_EMBED_MODEL", "qwen3-embedding:4b"),
        "OLLAMA_TEMPERATURE": _float_opt("OLLAMA_TEMPERATURE"),
        # Storage
        "UPLOAD_DIR": _env("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "storage", "uploads")),
        "CHROMA_PERSIST_DIR": _env(
            "CHROMA_PERSIST_DIR", os.path.join(os.path.dirname(__file__), "storage", "chroma")
        ),
        "CHROMA_COLLECTION": _env("CHROMA_COLLECTION", "enterprise_qa"),
        # RAG（部署级可调）
        "RAG_TOP_K": _int("RAG_TOP_K", 5),
        "RAG_CHUNK_SIZE": _int("RAG_CHUNK_SIZE", 1000),
        "RAG_CHUNK_OVERLAP": _int("RAG_CHUNK_OVERLAP", 150),
        "RAG_MAX_DISTANCE": _float_opt("RAG_MAX_DISTANCE"),
        "RAG_PROMPT_EXTRA": _env("RAG_PROMPT_EXTRA", "") or "",
        "MAX_QUESTION_LENGTH": _int("MAX_QUESTION_LENGTH", 8000),
        # 登录限流（每 IP 每窗口）
        "LOGIN_RATE_LIMIT_MAX": _int("LOGIN_RATE_LIMIT_MAX", 30),
        "LOGIN_RATE_LIMIT_WINDOW_SEC": _int("LOGIN_RATE_LIMIT_WINDOW_SEC", 60),
        # 异步入库线程数
        "INGEST_THREAD_WORKERS": _int("INGEST_THREAD_WORKERS", 2),
        # 指标（留空则不做鉴权，仅建议内网暴露 /api/metrics）
        "METRICS_TOKEN": _env("METRICS_TOKEN", "") or "",
    }

