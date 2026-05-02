-- 知识库表 + 文档归属（在已部署 01_schema 的库上执行）
USE `db_enterprise_qa`;

CREATE TABLE IF NOT EXISTS `knowledge_bases` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `name` VARCHAR(128) NOT NULL COMMENT '展示名称',
  `description` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '说明',
  `collection_name` VARCHAR(128) NOT NULL COMMENT 'Chroma collection 名',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_kb_collection` (`collection_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

INSERT IGNORE INTO `knowledge_bases` (`id`, `name`, `description`, `collection_name`)
VALUES (1, '默认知识库', '系统预置，与原有 Chroma 集合 enterprise_qa 一致', 'enterprise_qa');

ALTER TABLE `documents` ADD COLUMN `knowledge_base_id` INT NULL COMMENT '所属知识库' AFTER `id`;

UPDATE `documents` SET `knowledge_base_id` = 1 WHERE `knowledge_base_id` IS NULL;

ALTER TABLE `documents`
  MODIFY `knowledge_base_id` INT NOT NULL,
  ADD KEY `idx_documents_kb` (`knowledge_base_id`),
  ADD CONSTRAINT `fk_documents_knowledge_base` FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases` (`id`);
