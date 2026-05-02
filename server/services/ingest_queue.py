"""
文档向量化异步入库（线程池 + Flask app_context）。

说明：适合单租户自部署；多副本部署时应改为 Redis 队列 + 独立 worker。
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from flask import Flask

_log = logging.getLogger(__name__)
_executor: ThreadPoolExecutor | None = None


def init_ingest_executor(app: Flask) -> None:
    global _executor
    if _executor is None:
        workers = int(app.config.get("INGEST_THREAD_WORKERS", 2) or 2)
        _executor = ThreadPoolExecutor(max_workers=max(1, workers), thread_name_prefix="ingest")


def shutdown_ingest_executor() -> None:
    global _executor
    if _executor:
        _executor.shutdown(wait=False, cancel_futures=False)
        _executor = None


def submit_document_ingest(app: Flask, doc_id: int) -> None:
    if _executor is None:
        init_ingest_executor(app)

    def run() -> None:
        with app.app_context():
            from services.ingest_jobs import run_ingest_for_document

            try:
                run_ingest_for_document(doc_id)
            except Exception:
                _log.exception("ingest job failed doc_id=%s", doc_id)

    _executor.submit(run)
