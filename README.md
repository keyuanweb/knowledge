# Enterprise QA（企业知识库 RAG）

单租户、可自部署：Vue 3 前端 + Flask 后端 + MySQL + Chroma + Ollama。

## 目录结构

| 目录 | 说明 |
|------|------|
| `client/` | 前端（Vite + Vue） |
| `server/` | 后端 API 与 RAG |
| `docs/` | 部署与 API 文档 |
| `deploy/` | Nginx 等示例配置 |

## 快速开始

1. **数据库**：执行 `server/sql/01_schema.sql`、`02_seed.sql`（老库按需 `03`、`04`）。  
2. **后端**：见 [`server/README.md`](server/README.md)。  
3. **前端**：进入 `client/` 执行 `npm install`、`npm run dev`。  
4. **Docker**：仓库根目录 `docker-compose.yml` 与 [`docs/DEPLOY_SELF_HOSTED.md`](docs/DEPLOY_SELF_HOSTED.md)。

## 推送到 GitHub

在 [GitHub](https://github.com/new) 新建空仓库后，在仓库根目录执行：

```bash
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git branch -M main
git push -u origin main
```

若使用 SSH：`git remote add origin git@github.com:<用户名>/<仓库名>.git`
