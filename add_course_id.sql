-- 添加课程关联字段迁移
-- 执行方式: 在服务器上 psql -U postgres -d essay_system -f add_course_id.sql
-- 或通过 docker exec pg psql -U postgres -d essay_system -f /tmp/add_course_id.sql

-- 1. essay_tasks 表添加 course_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'essay_tasks' AND column_name = 'course_id'
    ) THEN
        ALTER TABLE essay_tasks ADD COLUMN course_id INTEGER;
        ALTER TABLE essay_tasks ADD CONSTRAINT fk_essay_tasks_course
            FOREIGN KEY (course_id) REFERENCES classes(id);
        CREATE INDEX idx_essay_tasks_course_id ON essay_tasks (course_id);
    END IF;
END $$;

-- 2. essays 表添加 course_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'essays' AND column_name = 'course_id'
    ) THEN
        ALTER TABLE essays ADD COLUMN course_id INTEGER;
        ALTER TABLE essays ADD CONSTRAINT fk_essays_course
            FOREIGN KEY (course_id) REFERENCES classes(id);
        CREATE INDEX idx_essays_course_id ON essays (course_id);
    END IF;
END $$;

-- 3. 回填数据：根据 essay_tasks.course_name 匹配 classes.name 关联已有任务
UPDATE essay_tasks t
SET course_id = c.id
FROM classes c
WHERE t.course_id IS NULL
  AND t.course_name <> ''
  AND t.course_name = c.name;

-- 4. 回填数据：根据任务关联回填作文课程
UPDATE essays e
SET course_id = t.course_id
FROM essay_tasks t
WHERE e.course_id IS NULL
  AND e.task_id = t.id
  AND t.course_id IS NOT NULL;
