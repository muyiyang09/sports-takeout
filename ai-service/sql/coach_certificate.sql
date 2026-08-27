-- 教练证书表（证书审核 Agent 数据源）
-- 用途：教练入驻提交的证书（国职/国际/急救证）落库，证书审核 Agent 审核后回写 status。

CREATE TABLE IF NOT EXISTS `coach_certificate` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT,
    `coach_id`    BIGINT       NOT NULL COMMENT '教练 ID',
    `cert_type`   VARCHAR(32)  NOT NULL COMMENT '证书类型：国职/国际认证/急救证',
    `cert_number` VARCHAR(64)  NOT NULL COMMENT '证书编号',
    `holder_name` VARCHAR(64)  NOT NULL COMMENT '持有人姓名',
    `image_url`   VARCHAR(255) DEFAULT NULL COMMENT '证书图片 URL（OCR）',
    `status`      TINYINT      NOT NULL DEFAULT 0 COMMENT '0待审核 1通过 2拒绝',
    `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    PRIMARY KEY (`id`),
    KEY `idx_coach` (`coach_id`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教练证书';
