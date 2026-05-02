# Enterprise QA（LangChain RAG · 单租户自部署）

## 1. 环境要求

- Python 3.10+（建议 3.11）
- MySQL 8
- Ollama（可访问 `http://localhost:11434` 或环境变量 `OLLAMA_BASE_URL`）
  - LLM：`qwen3:8b`（可配置 `OLLAMA_LLM_MODEL`）
  - Embedding：`qwen3-embedding:4b`（可配置 `OLLAMA_EMBED_MODEL`）

## 2. 初始化数据库

1. 执行 SQL（全新库）  
   - `server/sql/01_schema.sql`  
   - `server/sql/02_seed.sql`  
2. 若从**极老版本**升级且缺少「知识库」相关列，再执行 `server/sql/03_knowledge_bases.sql`（全新 `01_schema` 已包含时可跳过）。  
3. 若从**旧版 documents** 升级（无 `storage_path` / `ingest_error` / `audit_logs`），执行 `server/sql/04_commercial.sql`。

默认测试账号（**仅开发环境**；生产请修改密码）：

- 管理员：`admin` / `123456`
- 普通用户：`user1` / `123456`

## 3. 本地开发运行

进入 `server/`：

```bash
pip install -r requirements.txt
```

常用环境变量：

| 变量 | 说明 |
|------|------|
| `MYSQL_*` | 数据库连接 |
| `JWT_SECRET` | JWT 密钥（生产须足够长） |
| `FLASK_DEBUG` | `1` 开发 / `0` 生产 |
| `CORS_ORIGINS` | 允许的前端源，逗号分隔 |
| `OLLAMA_BASE_URL` | Ollama 地址 |
| `MAX_UPLOAD_BYTES` | 上传上限（字节），默认约 50MB |
| `RAG_TOP_K` / `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | 检索与切分 |
| `RAG_MAX_DISTANCE` | 可选，Chroma 距离上限过滤 |
| `METRICS_TOKEN` | 非空时 `/api/metrics` 需 Bearer |
| `LOGIN_RATE_LIMIT_*` | 登录限流次数与窗口（秒） |

启动开发服务：

```bash
python main.py
```

## 4. 生产运行（Gunicorn）

```bash
cd server
gunicorn -b 0.0.0.0:5000 -w 2 --threads 4 --timeout 300 wsgi:app
```

或使用 `deploy/gunicorn.conf.py`：

```bash
gunicorn -c deploy/gunicorn.conf.py wsgi:app
```

流式问答经 Nginx 反向代理时须关闭缓冲，示例见仓库根目录 `deploy/nginx-streaming.example.conf`。

## 5. 接口与健康检查

- 健康检查：`GET /api/health`（分项检查 MySQL、Ollama、Chroma；失败时 HTTP 503）  
- 指标：`GET /api/metrics`（Prometheus 文本）  
- 接口列表见仓库 [`docs/API.md`](../docs/API.md)

主要业务接口：

- 登录：`POST /api/auth/login`
- 当前用户：`GET /api/auth/me`
- 管理员上传：`POST /api/admin/docs/upload`（form-data：`file`、`knowledge_base_id`；**异步入库**，返回 `status` 枚举值及 `status_label` 中文）
- 重建索引：`POST /api/admin/docs/<id>/reindex`
- 问答：`POST /api/chat/ask`（JSON：`question`、`knowledge_base_id`，NDJSON 流）

## 6. 存储目录

- Chroma：`server/storage/chroma/`（可用 `CHROMA_PERSIST_DIR` 覆盖）
- 上传文件：`server/storage/uploads/`（可用 `UPLOAD_DIR` 覆盖）

## 7. Docker 与完整自部署

见仓库根目录：

- `docker-compose.yml`
- `.env.example`
- [`docs/DEPLOY_SELF_HOSTED.md`](../docs/DEPLOY_SELF_HOSTED.md)

## 8. 验收建议

1. 执行 `01_schema.sql`、`02_seed.sql`（及按需 `03`/`04`）。  
2. 拉取 Ollama 模型：`ollama pull qwen3:8b`、`ollama pull qwen3-embedding:4b`。  
3. 启动后端与前端，管理员登录后在「文档管理」上传 txt/md/pdf/docx。  
4. 刷新列表直至状态为「已入库」（`status=indexed`，见 `DocumentStatus`）。  
5. 在「智能问答」选择知识库提问，确认流式回答与 sources。

## 9. 冒烟测试

```bash
cd server
python -m unittest discover -s tests -v
```
