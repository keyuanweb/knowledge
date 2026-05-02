"""文档状态枚举与中文标签。"""

import unittest

from models.document_status import DocumentStatus, status_label_zh


class TestDocumentStatus(unittest.TestCase):
    def test_labels(self) -> None:
        self.assertEqual(status_label_zh(DocumentStatus.PENDING.value), "待入库")
        self.assertEqual(status_label_zh(DocumentStatus.PROCESSING.value), "入库中")
        self.assertEqual(status_label_zh(DocumentStatus.INDEXED.value), "已入库")
        self.assertEqual(status_label_zh(DocumentStatus.FAILED.value), "失败")
        self.assertEqual(status_label_zh(DocumentStatus.UPLOADED.value), "待入库")

    def test_enum_values_stable(self) -> None:
        self.assertEqual(DocumentStatus.PENDING.value, "pending")


if __name__ == "__main__":
    unittest.main()
