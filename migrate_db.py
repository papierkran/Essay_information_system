# -*- coding: utf-8 -*-
"""数据库迁移脚本：应用索引和约束变更。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import engine, DATABASE_URL
from sqlalchemy import text

MIGRATIONS = [
    # 1. 添加索引
    {
        "name": "idx_essays_status",
        "sql": "CREATE INDEX IF NOT EXISTS idx_essays_status ON essays (status);",
    },
    {
        "name": "idx_essays_collected_by",
        "sql": "CREATE INDEX IF NOT EXISTS idx_essays_collected_by ON essays (collected_by);",
    },
    {
        "name": "idx_essays_grade",
        "sql": "CREATE INDEX IF NOT EXISTS idx_essays_grade ON essays (grade);",
    },
    {
        "name": "idx_essays_created_at",
        "sql": "CREATE INDEX IF NOT EXISTS idx_essays_created_at ON essays (created_at);",
    },
    # 2. 添加 user_classes 唯一约束（先清理重复数据）
    {
        "name": "clean_dup_user_classes",
        "sql": """
            DELETE FROM user_classes a
            USING user_classes b
            WHERE a.id > b.id
              AND a.user_id = b.user_id
              AND a.class_id = b.class_id
              AND a.role_in_class = b.role_in_class;
        """,
    },
    {
        "name": "uq_user_class_role",
        "sql": """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_class_role'
                ) THEN
                    ALTER TABLE user_classes
                    ADD CONSTRAINT uq_user_class_role
                    UNIQUE (user_id, class_id, role_in_class);
                END IF;
            END $$;
        """,
    },
    # 3. 添加 essays.status CHECK 约束
    {
        "name": "ck_essays_status",
        "sql": """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'ck_essays_status'
                ) THEN
                    -- 先修正不符合约束的数据
                    UPDATE essays SET status = 'corrected'
                        WHERE status NOT IN ('pending', 'corrected');
                    UPDATE essays SET status = 'pending'
                        WHERE status IS NULL OR status = '';

                    ALTER TABLE essays
                    ADD CONSTRAINT ck_essays_status
                    CHECK (status IN ('pending', 'corrected'));
                END IF;
            END $$;
        """,
    },
    # 4. 创建 essay_tasks 表（作文收集任务）
    {
        "name": "create_essay_tasks",
        "sql": """
            CREATE TABLE IF NOT EXISTS essay_tasks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                grade VARCHAR(20) NOT NULL,
                essay_number INTEGER DEFAULT 1,
                essay_topic VARCHAR(200) DEFAULT '',
                course_name VARCHAR(100) DEFAULT '',
                teaching_mode VARCHAR(10) DEFAULT '线下',
                deadline TIMESTAMP,
                is_active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """,
    },
    {
        "name": "idx_essay_tasks_is_active",
        "sql": "CREATE INDEX IF NOT EXISTS idx_essay_tasks_is_active ON essay_tasks (is_active);",
    },
    # 5. 添加 essays.task_id 字段
    {
        "name": "add_essays_task_id",
        "sql": """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'essays' AND column_name = 'task_id'
                ) THEN
                    ALTER TABLE essays ADD COLUMN task_id INTEGER;
                    ALTER TABLE essays ADD CONSTRAINT fk_essays_task
                        FOREIGN KEY (task_id) REFERENCES essay_tasks(id);
                    CREATE INDEX idx_essays_task_id ON essays (task_id);
                END IF;
            END $$;
        """,
    },
    # 6. 迁移旧数据：如果存在essay_templates表，将其数据迁移到essay_tasks
    {
        "name": "migrate_templates_to_tasks",
        "sql": """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'essay_templates'
                ) THEN
                    -- 迁移模板数据到任务表
                    INSERT INTO essay_tasks (id, name, grade, essay_number, essay_topic, course_name, teaching_mode, deadline, is_active, created_at, updated_at)
                    SELECT id, name, grade, essay_number, essay_topic, course_name, teaching_mode, deadline, is_active, created_at, updated_at
                    FROM essay_templates
                    ON CONFLICT (id) DO NOTHING;
                    
                    -- 如果essays表有template_id字段，迁移为task_id
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'essays' AND column_name = 'template_id'
                    ) THEN
                        UPDATE essays SET task_id = template_id WHERE task_id IS NULL AND template_id IS NOT NULL;
                    END IF;
                END IF;
            END $$;
        """,
    },
]


def main():
    print(f"连接数据库: {DATABASE_URL.split('@')[1]}")

    with engine.connect() as conn:
        for mig in MIGRATIONS:
            print(f"执行: {mig['name']} ...", end=" ")
            try:
                conn.execute(text(mig["sql"]))
                conn.commit()
                print("✅")
            except Exception as e:
                print(f"❌ {e}")

    print("\n迁移完成。")


if __name__ == "__main__":
    main()
