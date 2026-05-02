"""
文档向量化状态枚举。

数据库存储值为枚举成员的 value（小写英文键），对外展示中文用 status_label_zh。
"""

from __future__ import annotations

from enum import Enum


class DocumentStatus(str, Enum):
    """与表 documents.status 取值一致。"""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    UPLOADED = "uploaded"  # 旧版兼容，等价于待入库

    @classmethod
    def from_raw(cls, raw: str | None) -> DocumentStatus | None:
        if not raw:
            return None
        try:
            return cls(raw)
        except ValueError:
            return None


# 枚举 value -> 中文
STATUS_LABEL_ZH: dict[str, str] = {
    DocumentStatus.PENDING.value: "待入库",
    DocumentStatus.PROCESSING.value: "入库中",
    DocumentStatus.INDEXED.value: "已入库",
    DocumentStatus.FAILED.value: "失败",
    DocumentStatus.UPLOADED.value: "待入库",
}


def status_label_zh(raw: str | None) -> str:
    """将数据库中的状态值转为中文说明。"""
    key = (raw or "").strip()
    return STATUS_LABEL_ZH.get(key, key or "未知")
