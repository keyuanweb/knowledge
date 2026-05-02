"""
应用工厂与路由注册冒烟测试（不依赖 MySQL 运行时可跳过依赖检查）。
"""

import os
import unittest


class TestCreateApp(unittest.TestCase):
    def test_create_app_imports(self) -> None:
        os.environ.setdefault("FLASK_DEBUG", "1")
        os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
        os.environ.setdefault("MYSQL_PORT", "3306")
        from app import create_app

        app = create_app()
        self.assertIsNotNone(app)
        self.assertTrue(hasattr(app, "url_map"))

    def test_blueprints_registered(self) -> None:
        os.environ.setdefault("FLASK_DEBUG", "1")
        from app import create_app

        app = create_app()
        rules = {r.rule for r in app.url_map.iter_rules()}
        self.assertIn("/api/health", rules)
        self.assertIn("/api/metrics", rules)
        self.assertIn("/api/auth/login", rules)


if __name__ == "__main__":
    unittest.main()
