"""
WSGI 入口，供 gunicorn 使用：gunicorn -c deploy/gunicorn.conf.py wsgi:app
"""

from app import create_app

app = create_app()
