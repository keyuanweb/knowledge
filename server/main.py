"""
项目启动入口。

说明：
- 本项目后端使用 Flask + MySQL + Chroma + Ollama。
- 运行方式见 server/README.md。
"""

from app import create_app


def main():
    """
    启动 Flask 开发服务器。

    注意：
    - 生产环境请使用 gunicorn/uwsgi 等方式部署。
    """

    app = create_app()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
