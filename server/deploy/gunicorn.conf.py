# Gunicorn 配置（单租户自部署参考）
# 用法：在 server 目录下 gunicorn -c deploy/gunicorn.conf.py wsgi:app
import multiprocessing

bind = "0.0.0.0:5000"
workers = int(__import__("os").getenv("GUNICORN_WORKERS", str(max(2, multiprocessing.cpu_count() // 2))))
threads = 4
timeout = 300
graceful_timeout = 120
keepalive = 5
worker_class = "gthread"
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
