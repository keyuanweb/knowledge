"""
文件解析服务：将上传文件转换为纯文本。

支持：
- txt
- md
- pdf（依赖 pypdf）
- docx（依赖 python-docx）
"""

from __future__ import annotations

import os


class FileLoader:
    """
    文档解析器。
    """

    @staticmethod
    def detect_type(filename: str) -> str:
        """根据文件名后缀判断类型。"""

        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        return ext or "unknown"

    @staticmethod
    def load_text(file_path: str, file_type: str) -> str:
        """
        将文件解析为文本。
        """

        file_type = (file_type or "").lower()
        if file_type in ("txt", "md"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        if file_type == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            parts: list[str] = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            return "\n".join(parts)

        if file_type == "docx":
            import docx

            d = docx.Document(file_path)
            return "\n".join([p.text for p in d.paragraphs])

        raise ValueError(f"不支持的文件类型：{file_type}")

