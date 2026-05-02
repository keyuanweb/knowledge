# HTTP API 摘要（OpenAPI 风格速查）

Base URL：`/api`（与前端 `VITE_API_BASE_URL` 一致，默认 `http://localhost:5000/api`）。

## 健康与指标

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | MySQL / Ollama / Chroma 检查；失败时 503 |
| GET | `/metrics` | Prometheus 文本；若配置 `METRICS_TOKEN` 则需 Bearer |

## 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | JSON：`username`, `password`；限流见部署说明 |
| GET | `/auth/me` | Bearer Token |

## 问答（需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/chat/knowledge-bases` | 可选知识库列表 |
| POST | `/chat/ask` | JSON：`question`, `knowledge_base_id`；NDJSON 流 |
| GET | `/chat/history` | 查询参数 `limit` |

## 管理（需 admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/stats` | 统计 |
| GET | `/admin/audit-logs` | 审计列表，`?limit=` |
| GET | `/admin/docs` | 文档列表；每条含 `status`（枚举值）、`status_label`（中文） |
| POST | `/admin/docs/upload` | multipart：`file`, `knowledge_base_id`, `title` 可选 |
| POST | `/admin/docs/<id>/reindex` | 重建向量 |
| DELETE | `/admin/docs/<id>` | 删除文档 |
| GET/POST/DELETE | `/admin/knowledge-bases` … | 知识库 CRUD |
| GET/PATCH/DELETE | `/admin/users` … | 用户管理 |

完整错误语义以 JSON 字段 `ok`, `message` 为准。
