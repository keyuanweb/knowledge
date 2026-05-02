# 单租户自部署指南

## 1. 架构说明

- **后端**：Flask + Gunicorn（`wsgi:app`），MySQL 8，Chroma 持久化卷，Ollama（建议同网段或宿主机）。
- **前端**：Vite 构建静态资源，由 Nginx 托管（或使用开发服务器仅内网调试）。

## 2. 数据库初始化

全新库按顺序执行：

1. `server/sql/01_schema.sql`
2. `server/sql/02_seed.sql`
3. `server/sql/03_knowledge_bases.sql`

若从**旧版**仅有 `documents` 且无 `storage_path` / `ingest_error` / `audit_logs` 的库升级，再执行一次：

4. `server/sql/04_commercial.sql`（若列已存在会报错，按提示跳过已执行语句）

## 3. Docker Compose（参考）

仓库根目录：

```bash
cp .env.example .env
# 编辑 .env：JWT_SECRET、MYSQL_ROOT_PASSWORD、OLLAMA_BASE_URL 等
docker compose up -d --build
```

说明：

- Ollama 默认指向 `http://host.docker.internal:11434`（Windows / Mac）。Linux 请改为宿主机可达地址。
- 首次启动 MySQL 会挂载执行 `01`～`03` SQL；**不要**将 `04_commercial.sql` 放入 initdb（全新 `01` 已含新列时会导致重复列错误）。
- 应用数据卷：`chroma_data`、`uploads_data`。

## 4. 本机 / 虚拟机（不用 Docker）

```bash
cd server
pip install -r requirements.txt
# 配置环境变量，见 .env.example
gunicorn -b 0.0.0.0:5000 -w 2 --threads 4 --timeout 300 wsgi:app
```

开发仍可用 `python main.py`（不推荐生产）。

## 5. 健康检查与指标

- `GET /api/health`：返回 MySQL、Ollama、Chroma 分项状态；任一项失败时 HTTP **503**（便于编排探针）。
- `GET /api/metrics`：Prometheus 文本；若设置环境变量 `METRICS_TOKEN`，请求需带 `Authorization: Bearer <token>`。

## 6. 备份与恢复（建议写入运维手册）

1. **MySQL**：定期逻辑备份（`mysqldump`）数据库 `db_enterprise_qa`。
2. **文件与向量**：与容器卷或目录一致备份  
   - `storage/uploads/`  
   - `storage/chroma/`  
3. 恢复顺序：先停应用 → 还原 MySQL → 还原上述目录 → 启动应用。  
4. **更换 embedding 模型**后需对全部文档**重新向量化**（界面「重建索引」或重新上传策略），并在变更说明中记录模型版本。

## 7. 流式问答与 Nginx

流式接口 `POST /api/chat/ask` 必须在代理层**关闭缓冲**，示例见 [`deploy/nginx-streaming.example.conf`](../deploy/nginx-streaming.example.conf)。

## 8. 文档异步入库

上传接口立即返回 `pending`，向量化在后台线程执行。失败时状态为 `failed`，可在文档列表查看原因，并支持「重建索引」（需本地仍保留上传文件）。

## 9. 安全建议

- 生产环境 `FLASK_DEBUG=0`，`JWT_SECRET` 使用高强度随机串。
- 对外服务启用 **HTTPS**；限制 `CORS_ORIGINS` 为实际前端域名。
- 登录接口带简单 **IP 限流**（进程内，多 worker 时各进程独立计数；高安全场景可改为 Redis 等共享存储）。

## 10. 前端品牌化（可选）

在 `client` 目录创建 `.env`：

```env
VITE_APP_TITLE=贵司知识库
VITE_APP_SUBTITLE=内部 RAG 问答
VITE_API_BASE_URL=https://rag.example.com/api
```

重新 `npm run build` 即可。
