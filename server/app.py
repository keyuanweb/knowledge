"""
Flask 应用工厂。

说明：
- 为了便于入门学习，本项目使用“应用工厂”模式组织代码。
- 所有蓝图（routes）与扩展（extensions）都在这里完成注册。
"""

from __future__ import annotations

import time
import uuid
import warnings

from flask import Flask, Response, g, jsonify, request
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import RequestEntityTooLarge

from config import load_config
from extensions import init_extensions
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.chat import chat_bp
from services.errors import AuthRequiredError, ForbiddenError
from services.health_service import full_health
from services.ingest_queue import init_ingest_executor
from services.metrics_service import inc_counter, inc_error, observe_latency
from services.rate_limit import FixedWindowLimiter


def create_app() -> Flask:
    """
    创建并配置 Flask 应用实例。
    """

    app = Flask(__name__)
    app.config.update(load_config())

    if not app.debug:
        j = str(app.config.get("JWT_SECRET") or "")
        if len(j) < 24:
            warnings.warn(
                "JWT_SECRET 长度过短，生产环境请设置至少 24 字节的随机密钥（环境变量 JWT_SECRET）",
                stacklevel=1,
            )

    # 初始化扩展（数据库/JWT/CORS 等）
    init_extensions(app)

    app.extensions["login_limiter"] = FixedWindowLimiter(
        int(app.config.get("LOGIN_RATE_LIMIT_MAX", 30)),
        float(app.config.get("LOGIN_RATE_LIMIT_WINDOW_SEC", 60)),
    )
    init_ingest_executor(app)

    # 注册路由蓝图
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.before_request
    def _request_start():
        g.request_id = str(uuid.uuid4())[:12]
        g._t0 = time.perf_counter()

    @app.after_request
    def _request_end(resp):
        try:
            if request.path.startswith("/api/") and request.path != "/api/metrics":
                ep = request.endpoint or "unknown"
                elapsed_ms = (time.perf_counter() - getattr(g, "_t0", time.perf_counter())) * 1000
                observe_latency(ep, elapsed_ms)
                inc_counter(ep)
                if resp.status_code >= 400:
                    inc_error(ep)
                app.logger.info(
                    "request id=%s %s %s -> %s %.2fms",
                    getattr(g, "request_id", "-"),
                    request.method,
                    request.path,
                    resp.status_code,
                    elapsed_ms,
                )
        except Exception:
            pass
        return resp

    @app.get("/api/health")
    def health():
        """健康检查：MySQL、Ollama、Chroma。"""

        body = full_health()
        status = 200 if body.get("ok") else 503
        return jsonify(body), status

    @app.get("/api/metrics")
    def metrics():
        """
        Prometheus 文本指标。若配置 METRICS_TOKEN，则需在 Authorization: Bearer <token>。
        """

        tok = (app.config.get("METRICS_TOKEN") or "").strip()
        if tok:
            auth = request.headers.get("Authorization") or ""
            if auth != f"Bearer {tok}":
                return jsonify({"ok": False, "message": "unauthorized"}), 401
        from services.metrics_service import prometheus_text

        return Response(prometheus_text(), mimetype="text/plain; charset=utf-8")

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_e: RequestEntityTooLarge):
        return jsonify({"ok": False, "message": "上传文件超过服务器限制（MAX_UPLOAD_BYTES）"}), 413

    @app.errorhandler(Exception)
    def handle_error(e: Exception):
        """
        统一异常处理，返回 JSON。

        说明：
        - 这里不做复杂的错误码体系，保持适中复杂度；
        - 生产环境建议区分业务异常/系统异常并隐藏敏感信息。
        """

        # 常见错误分类，便于前端做正确提示
        if isinstance(e, AuthRequiredError):
            return jsonify({"ok": False, "message": str(e)}), 401
        if isinstance(e, ForbiddenError):
            return jsonify({"ok": False, "message": str(e)}), 403
        if isinstance(e, ValueError):
            return jsonify({"ok": False, "message": str(e)}), 400
        if isinstance(e, OperationalError):
            # 常见场景：数据库未启动/未建库建表/连接参数错误
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "数据库连接失败或表不存在，请先执行 server/sql/01_schema.sql、02_seed.sql；老库请再执行 03_knowledge_bases.sql 与 04_commercial.sql",
                    }
                ),
                500,
            )

        return jsonify({"ok": False, "message": str(e)}), 500

    return app
