-- 从旧版 01_schema 升级时使用（全新安装若已含下列列可跳过）
USE `db_enterprise_qa`;

ALTER TABLE `documents`
  ADD COLUMN `storage_path` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '相对 uploads 的存储文件名' AFTER `file_type`,
  ADD COLUMN `ingest_error` TEXT NULL COMMENT '异步入库失败原因' AFTER `status`;

CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `actor_user_id` INT NOT NULL COMMENT '操作者用户ID',
  `action` VARCHAR(64) NOT NULL COMMENT '动作类型',
  `detail` TEXT NULL COMMENT 'JSON 或简短说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间',
  PRIMARY KEY (`id`),
  KEY `idx_audit_created` (`created_at`),
  KEY `idx_audit_actor` (`actor_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理操作审计';
