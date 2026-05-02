-- 数据库：db_enterprise_qa
-- MySQL 8.x
-- 说明：可直接执行本文件完成建库建表

CREATE DATABASE IF NOT EXISTS `db_enterprise_qa`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE `db_enterprise_qa`;

-- 用户表：管理员/普通用户
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username` VARCHAR(64) NOT NULL COMMENT '用户名',
  `password_md5` CHAR(32) NOT NULL COMMENT 'MD5 密码（按需求）',
  `role` VARCHAR(16) NOT NULL DEFAULT 'user' COMMENT '角色：admin/user',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 知识库：每个库对应独立 Chroma collection
CREATE TABLE IF NOT EXISTS `knowledge_bases` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `name` VARCHAR(128) NOT NULL COMMENT '展示名称',
  `description` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '说明',
  `collection_name` VARCHAR(128) NOT NULL COMMENT 'Chroma collection 名',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_kb_collection` (`collection_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

INSERT INTO `knowledge_bases` (`id`, `name`, `description`, `collection_name`)
VALUES (1, '默认知识库', '系统预置', 'enterprise_qa')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- 文档表：上传文件的元信息
CREATE TABLE IF NOT EXISTS `documents` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `knowledge_base_id` INT NOT NULL COMMENT '所属知识库',
  `title` VARCHAR(255) NOT NULL COMMENT '文档标题',
  `filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `file_type` VARCHAR(32) NOT NULL COMMENT '文件类型：pdf/docx/md/txt',
  `storage_path` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '相对 uploads 的存储文件名',
  `status` VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态枚举值 pending/processing/indexed/failed/uploaded，中文见 API status_label',
  `ingest_error` TEXT NULL COMMENT '入库失败原因',
  `created_by` INT NOT NULL COMMENT '创建者用户ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_documents_created_by` (`created_by`),
  KEY `idx_documents_kb` (`knowledge_base_id`),
  CONSTRAINT `fk_documents_knowledge_base` FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档表';

-- 文档切片表：用于审计与统计（检索以向量库为准）
CREATE TABLE IF NOT EXISTS `doc_chunks` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `doc_id` INT NOT NULL COMMENT '文档ID',
  `chunk_index` INT NOT NULL COMMENT '切片序号',
  `content` LONGTEXT NOT NULL COMMENT '切片内容',
  `content_md5` CHAR(32) NOT NULL COMMENT '切片内容MD5（用于去重）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_doc_chunks_doc_id` (`doc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档切片表';

-- 管理操作审计
CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `actor_user_id` INT NOT NULL COMMENT '操作者用户ID',
  `action` VARCHAR(64) NOT NULL COMMENT '动作类型',
  `detail` TEXT NULL COMMENT 'JSON 或简短说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间',
  PRIMARY KEY (`id`),
  KEY `idx_audit_created` (`created_at`),
  KEY `idx_audit_actor` (`actor_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志';

-- 问答日志表：用于后台统计/复盘
CREATE TABLE IF NOT EXISTS `chat_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `question` LONGTEXT NOT NULL COMMENT '用户问题',
  `answer` LONGTEXT NOT NULL COMMENT '模型回答',
  `sources_json` LONGTEXT NOT NULL COMMENT '来源JSON',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_chat_logs_user_id` (`user_id`),
  KEY `idx_chat_logs_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问答日志表';

