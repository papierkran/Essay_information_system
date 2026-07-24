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
