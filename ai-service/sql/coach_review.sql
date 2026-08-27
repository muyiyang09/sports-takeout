-- 教练评价表（评价摘要 Agent 数据源）
-- 用途：评价摘要 Agent（review_summary）从本表取评价做优缺点摘要。
-- 落地前：review_summary 用 mock 兜底；本表建好并灌入数据后，fetch_reviews 自动切真读。

CREATE TABLE IF NOT EXISTS `coach_review` (
    `id`         BIGINT      NOT NULL AUTO_INCREMENT,
    `coach_id`   BIGINT      NOT NULL COMMENT '教练 ID',
    `user_id`    VARCHAR(64) NOT NULL DEFAULT 'anon' COMMENT '评价用户 ID',
    `content`    TEXT        NOT NULL COMMENT '评价内容',
    `rating`     TINYINT     NOT NULL DEFAULT 5 COMMENT '评分 1~5',
    `created_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评价时间',
    PRIMARY KEY (`id`),
    KEY `idx_coach_created` (`coach_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教练评价';
