# -*- coding: utf-8 -*-
"""数据库迁移脚本：应用索引和约束变更。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import engine, DATABASE_URL
from sqlalchemy import text

MIGRATIONS = [
    # 0. 清理重复数据（为后续唯一约束做准备，保留每组中 id 最大的那条）
    {
        "name": "clean_dup_essays_for_unique",
        "sql": """
            DELETE FROM essays a
            USING essays b
            WHERE a.id < b.id
              AND a.class_id = b.class_id
              AND a.task_id IS NOT DISTINCT FROM b.task_id
              AND a.student_name = b.student_name
              AND a.essay_number = b.essay_number
              AND a.is_supplement = b.is_supplement;
        """,
    },
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
                        WHERE status NOT IN ('pending', 'confirming', 'corrected');
                    UPDATE essays SET status = 'pending'
                        WHERE status IS NULL OR status = '';

                    ALTER TABLE essays
                    ADD CONSTRAINT ck_essays_status
                    CHECK (status IN ('pending', 'confirming', 'corrected'));
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
    # 7. 所有表添加 deleted_at 软删除字段
    {
        "name": "add_deleted_at_columns",
        "sql": """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='essays' AND column_name='deleted_at') THEN
                    ALTER TABLE essays ADD COLUMN deleted_at TIMESTAMP;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='essay_tasks' AND column_name='deleted_at') THEN
                    ALTER TABLE essay_tasks ADD COLUMN deleted_at TIMESTAMP;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='deleted_at') THEN
                    ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organizations' AND column_name='deleted_at') THEN
                    ALTER TABLE organizations ADD COLUMN deleted_at TIMESTAMP;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='classes' AND column_name='deleted_at') THEN
                    ALTER TABLE classes ADD COLUMN deleted_at TIMESTAMP;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='user_classes' AND column_name='deleted_at') THEN
                    ALTER TABLE user_classes ADD COLUMN deleted_at TIMESTAMP;
                END IF;
            END $$;
        """,
    },
    {
        "name": "idx_essays_deleted_at",
        "sql": "CREATE INDEX IF NOT EXISTS idx_essays_deleted_at ON essays (deleted_at);",
    },
    # 8. essays 唯一约束（NULLS NOT DISTINCT，PG15+）
    {
        "name": "uq_essay_task_student",
        "sql": """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_essay_task_student'
                ) THEN
                    ALTER TABLE essays
                    ADD CONSTRAINT uq_essay_task_student
                    UNIQUE NULLS NOT DISTINCT (class_id, task_id, student_name, essay_number, is_supplement);
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
    # 9. 重建 operation_logs 表（匹配最新模型结构）
    {
        "name": "recreate_operation_logs",
        "sql": """
            DROP TABLE IF EXISTS operation_logs CASCADE;
            CREATE TABLE operation_logs (
                id SERIAL PRIMARY KEY,
                essay_id INTEGER,
                user_id INTEGER NOT NULL,
                action VARCHAR(20) NOT NULL,
                old_value TEXT DEFAULT '',
                new_value TEXT DEFAULT '',
                detail VARCHAR(500) DEFAULT '',
                batch_id VARCHAR(50),
                essay_ids TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT fk_operation_logs_essay FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE SET NULL,
                CONSTRAINT fk_operation_logs_user FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX idx_operation_logs_essay_id ON operation_logs (essay_id);
            CREATE INDEX idx_operation_logs_created_at ON operation_logs (created_at);
            CREATE INDEX idx_operation_logs_user_id ON operation_logs (user_id);
            CREATE INDEX idx_operation_logs_batch_id ON operation_logs (batch_id);
        """,
    },
    # 9. 允许 classes.org_id 为空
    {
        "name": "make_classes_org_id_nullable",
        "sql": "ALTER TABLE classes ALTER COLUMN org_id DROP NOT NULL;",
    },
    # 10. essay_tasks.name 唯一约束
    {
        "name": "uq_essay_tasks_name",
        "sql": """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_essay_tasks_name'
                ) THEN
                    ALTER TABLE essay_tasks ADD CONSTRAINT uq_essay_tasks_name UNIQUE (name);
                END IF;
            END $$;
        """,
    },
    # 11. 修改 essays 唯一约束，添加 essay_title（支持作文次数为0或空时同学生不同标题）
    {
        "name": "update_uq_essay_task_student_add_title",
        "sql": """
            DO $$
            BEGIN
                -- 删除旧约束
                IF EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_essay_task_student'
                ) THEN
                    ALTER TABLE essays DROP CONSTRAINT uq_essay_task_student;
                END IF;
                -- 添加新约束（包含 essay_title）
                ALTER TABLE essays
                ADD CONSTRAINT uq_essay_task_student
                UNIQUE NULLS NOT DISTINCT (class_id, task_id, student_name, essay_number, is_supplement, essay_title);
            END $$;
        """,
    },
    # 12. essays 添加 collector_note / reviewer_note 备注字段
    {
        "name": "add_essays_notes_columns",
        "sql": """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='essays' AND column_name='collector_note') THEN
                    ALTER TABLE essays ADD COLUMN collector_note TEXT DEFAULT '';
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='essays' AND column_name='reviewer_note') THEN
                    ALTER TABLE essays ADD COLUMN reviewer_note TEXT DEFAULT '';
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
