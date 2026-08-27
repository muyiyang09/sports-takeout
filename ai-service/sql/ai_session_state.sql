-- ai-service 会话状态灾备表（Checkpointer DB 兜底层）
-- 用途：Redis Checkpointer TTL 到期时，从这里读回会话 state 回填 Redis，防会话中断。
-- 注意：本表由 main.py lifespan 幂等建表（ensure_table），也可手动执行本文件。

CREATE TABLE IF NOT EXISTS `ai_session_state` (
    `thread_id`       VARCHAR(128) NOT NULL COMMENT '会话 thread_id',
    `checkpoint_json` TEXT         NOT NULL COMMENT 'CheckpointTuple 的 JSON',
    `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`thread_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 会话状态灾备（Checkpointer DB 兜底）';
