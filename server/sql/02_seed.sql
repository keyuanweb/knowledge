-- 测试数据（密码：123456，按需求使用 MD5）
-- 说明：先执行 01_schema.sql 再执行本文件

USE `db_enterprise_qa`;

-- 123456 的 MD5：e10adc3949ba59abbe56e057f20f883e

INSERT INTO `users` (`username`, `password_md5`, `role`)
VALUES
  ('admin', 'e10adc3949ba59abbe56e057f20f883e', 'admin'),
  ('user1', 'e10adc3949ba59abbe56e057f20f883e', 'user')
ON DUPLICATE KEY UPDATE
  `password_md5` = VALUES(`password_md5`),
  `role` = VALUES(`role`);

