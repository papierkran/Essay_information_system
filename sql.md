# 数据库设计文档（sql.md）

> 来源：`backend/app/models/models.py`（SQLAlchemy ORM 定义）
> 数据库：**PostgreSQL**（生产） / SQLite（本地可用）
> 说明：本项目使用 `Base.metadata.create_all()` 建表 + 轻量 ALTER 补列（`database.py:_migrate_existing_columns`），**无 Alembic 版本化迁移**。
> 更新：2026-08-06 —— `Class` 模型重构为 `Course`（表 `course`），相关 FK 同步变更。

---

## 一、表结构总览

| 表名 | 中文含义 | 说明 |
|------|---------|------|
| `organizations` | 培训班/机构 | 顶层组织单位 |
| `users` | 用户 | 支持多角色（admin/collector/reviewer，可逗号组合） |
| `course` | 课程 | 原 `classes` 班级表重构为课程表（隶属机构） |
| `user_classes` | 用户-课程关系 | 用户在课程中的角色（收集者绑定课程） |
| `essay_tasks` | 收集任务 | 一次作文收集活动（年级/第几次/主题/课程/截止） |
| `essays` | 作文 | 核心业务表，含原文/改后/状态/归属 |
| `essay_images` | 作文图片 | 图片二进制存数据库（LargeBinary） |
| `system_config` | 系统配置 | key-value JSON，存 OCR/LLM 配置 |
| `operation_logs` | 操作日志 | 审计日志（含批量操作） |

### 关系图（ER）

> 注：课程为独立表 `course`。`essays` 同时有 `class_id` 与 `course_id` 两列均指向 `course.id`（重构过渡期，见「四、设计说明」第 3 条）。

```
organizations 1─N users ─1 user_classes ─1 course
organizations 1─N course
course        1─N essay_tasks  (course_id 课程)
course        1─N essays       (course_id 课程)
course        1─N essays       (class_id 班级，过渡期字段)
essay_tasks   1─N essays
users         1─N essays (collected_by 收集者)
users         1─N essays (reviewer_id 批改者)
essays        1─N essay_images
essays        1─N operation_logs
users         1─N operation_logs
```

---

## 二、各表字段设计

> 通用约定：
> - 所有业务表均有 `id`（自增主键）、`created_at`、`updated_at`、`deleted_at`（软删除标记，NULL=未删除）
> - 软删除：逻辑删除，`deleted_at` 非空视为已删除

### 1. `organizations` — 培训班

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| name | VARCHAR(100) | NOT NULL | 机构名称 |
| desc | TEXT | 默认 '' | 描述 |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now, 更新时刷新 | 更新时间 |

### 2. `users` — 用户

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 登录名 |
| password_hash | VARCHAR(200) | NOT NULL | 密码哈希（SHA-256+salt，⚠ 建议升级 bcrypt） |
| nickname | VARCHAR(50) | 默认 '' | 昵称 |
| phone | VARCHAR(20) | 默认 '' | 电话 |
| role | VARCHAR(50) | 默认 'collector' | 角色：admin/collector/reviewer，多角色逗号分隔（如 "collector,reviewer"），文档中另有 guest（游客） |
| org_id | INTEGER | FK→organizations.id, 可空 | 所属机构 |
| is_active | BOOLEAN | 默认 true | 是否启用（禁用后登录与鉴权被拒） |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

### 3. `course` — 课程（原 classes 表重构）

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| org_id | INTEGER | FK→organizations.id, 可空 | 所属机构 |
| name | VARCHAR(100) | NOT NULL | 课程名称（如「初一语文」） |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

> ⚠ 重构说明：原 `Class` 模型（表 `classes`）已改名 `Course`（表 `course`），ORM 关系与前端组件同步调整（`AdminCourse.vue`）。**存量数据库中 `classes` 表需迁移**：新建 `course` 表并拷贝数据，或直接 RENAME（若 `classes` 与 `course` 语义一致可 `ALTER TABLE classes RENAME TO course`）。

### 4. `user_classes` — 用户-课程关系

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| user_id | INTEGER | FK→users.id, NOT NULL | 用户（收集者） |
| class_id | INTEGER | FK→course.id, NOT NULL | 课程（列名沿用历史，实际指向课程） |
| role_in_class | VARCHAR(20) | 默认 'collector' | 课程内角色（当前仅用 collector） |
| deleted_at | TIMESTAMP | NULL | 软删除 |

**唯一约束**：`uq_user_class_role` (user_id, class_id, role_in_class)

> ⚠ **使用状态（半启用）**：后端有读写接口（admin.py `/api/admin/courses/{course_id}/collectors`），但**前端无界面调用**；业务侧 `get_collector_classes()`（essays.py:229）定义后**零调用**。数据可见性（收集者只看自己负责课程）尚未生效，表中数据大概率为空。

### 5. `essay_tasks` — 收集任务

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| name | VARCHAR(100) | UNIQUE, NOT NULL | 任务名称 |
| grade | VARCHAR(20) | NOT NULL | 年级 |
| essay_number | INTEGER | 默认 1 | 第几次作文 |
| essay_topic | VARCHAR(200) | 默认 '' | 文章主题 |
| course_id | INTEGER | FK→course.id, 可空 | 关联课程 |
| teaching_mode | VARCHAR(10) | 默认 '线下' | 线下/线上（同一课程的提交方式） |
| deadline | TIMESTAMP | NULL | 收集截止时间 |
| is_active | BOOLEAN | 默认 false | 是否当前活跃任务 |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

> `course_name` 为 ORM 计算属性：`course = relationship("Course")` → `self.course.name`（`models.py:42-44`），不再落库。原 `course_name` 字符串字段已移除。

### 6. `essays` — 作文（核心表）

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| class_id | INTEGER | FK→course.id, NOT NULL | 所属班级（过渡期：实际指向课程表） |
| task_id | INTEGER | FK→essay_tasks.id, 可空 | 关联收集任务 |
| course_id | INTEGER | FK→course.id, 可空 | 直接关联课程（上传时优先取传入值，否则从任务继承，冗余存储） |
| grade | VARCHAR(20) | 默认 '' | 年级 |
| essay_number | INTEGER | 默认 1 | 第几次作文 |
| essay_title | VARCHAR(200) | 默认 '' | 作文标题 |
| student_name | VARCHAR(50) | NOT NULL | 学生姓名（⚠ 仅字符串，无独立学生表） |
| is_supplement | BOOLEAN | 默认 false | 是否补交 |
| teaching_mode | VARCHAR(10) | 默认 '线下' | 线下/线上 |
| remark | TEXT | 默认 '' | 备注（历史字段） |
| collector_note | TEXT | 默认 '' | 收集者备注 |
| reviewer_note | TEXT | 默认 '' | 批改者备注 |
| content_text | TEXT | 默认 '' | 原文文字内容 |
| content_file | VARCHAR(500) | 默认 '' | 原文文件相对路径（相对 upload_dir） |
| file_type | VARCHAR(10) | 默认 'text' | 内容类型：text/image/docx |
| collected_by | INTEGER | FK→users.id, NOT NULL | 收集者 |
| status | VARCHAR(20) | 默认 'pending' | 状态：pending/confirming/corrected |
| file_saved | BOOLEAN | 默认 true | 文件是否存在于磁盘 |
| corrected_text | TEXT | 默认 '' | 修改后文字内容 |
| reviewer_id | INTEGER | FK→users.id, 可空 | 批改者 |
| corrected_at | TIMESTAMP | NULL | 批改完成时间 |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

**索引**：

| 索引名 | 字段 |
|--------|------|
| idx_essays_status | status |
| idx_essays_collected_by | collected_by |
| idx_essays_grade | grade |
| idx_essays_created_at | created_at |
| idx_essays_task_id | task_id |
| idx_essays_deleted_at | deleted_at |

**约束**：
- 唯一约束 `uq_essay_task_student`：(class_id, task_id, student_name, essay_number, is_supplement, essay_title)
- 检查约束 `ck_essays_status`：`status IN ('pending','confirming','corrected')`

### 7. `essay_images` — 作文图片

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| essay_id | INTEGER | FK→essays.id, NOT NULL, 索引 | 所属作文 |
| filename | VARCHAR(200) | NOT NULL | 文件名 |
| image_data | BYTEA (LargeBinary) | NOT NULL | 图片二进制（⚠ 存 DB，体积膨胀风险） |
| created_at | TIMESTAMP | 默认 now | 创建时间 |

### 8. `system_config` — 系统配置

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| config_key | VARCHAR(100) | UNIQUE, NOT NULL | 配置键（如 ocr、llm_typo_fix、llm_editor） |
| config_value | TEXT | 默认 '{}' | 配置值（JSON 字符串，⚠ 含 API Key 明文） |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

### 9. `operation_logs` — 操作日志

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| essay_id | INTEGER | FK→essays.id, ON DELETE SET NULL, 可空 | 关联作文 |
| user_id | INTEGER | FK→users.id, NOT NULL | 操作人 |
| action | ENUM | NOT NULL | 操作类型（见下） |
| old_value | TEXT | 默认 '' | 变更前值（JSON） |
| new_value | TEXT | 默认 '' | 变更后值（JSON） |
| detail | VARCHAR(500) | 默认 '' | 操作详情 |
| batch_id | VARCHAR(50) | NULL | 批量操作分组 ID |
| essay_ids | TEXT | NULL | 批量涉及的作文 ID 列表（JSON 数组） |
| created_at | TIMESTAMP | 默认 now | 创建时间 |

**action 枚举值**：`创建 / 修改 / 删除 / 恢复 / 编辑 / 上传 / 批改 / OCR`（另有旧值 `EDIT`、`CORRECT` 兼容历史数据）

**索引**：

| 索引名 | 字段 |
|--------|------|
| idx_operation_logs_essay_id | essay_id |
| idx_operation_logs_created_at | created_at |
| idx_operation_logs_user_id | user_id |
| idx_operation_logs_batch_id | batch_id |

---

## 三、对应 PostgreSQL DDL 参考

> 以下为等价 PostgreSQL DDL（供建库/迁移参考）。实际建表由 SQLAlchemy `create_all` 生成，此处字段类型与约束保持一致。

```sql
-- 1. 培训班
CREATE TABLE organizations (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(100) NOT NULL,
  desc        TEXT DEFAULT '',
  deleted_at  TIMESTAMP,
  created_at  TIMESTAMP DEFAULT now(),
  updated_at  TIMESTAMP DEFAULT now()
);

-- 2. 用户
CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  username      VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(200) NOT NULL,
  nickname      VARCHAR(50) DEFAULT '',
  phone         VARCHAR(20) DEFAULT '',
  role          VARCHAR(50) DEFAULT 'collector',
  org_id        INTEGER REFERENCES organizations(id),
  is_active     BOOLEAN DEFAULT TRUE,
  deleted_at    TIMESTAMP,
  created_at    TIMESTAMP DEFAULT now(),
  updated_at    TIMESTAMP DEFAULT now()
);

-- 3. 课程（原班级表重构）
CREATE TABLE course (
  id          SERIAL PRIMARY KEY,
  org_id      INTEGER REFERENCES organizations(id),
  name        VARCHAR(100) NOT NULL,
  deleted_at  TIMESTAMP,
  created_at  TIMESTAMP DEFAULT now(),
  updated_at  TIMESTAMP DEFAULT now()
);

-- 4. 用户-课程关系
CREATE TABLE user_classes (
  id            SERIAL PRIMARY KEY,
  user_id       INTEGER NOT NULL REFERENCES users(id),
  class_id      INTEGER NOT NULL REFERENCES course(id),
  role_in_class VARCHAR(20) DEFAULT 'collector',
  deleted_at    TIMESTAMP,
  CONSTRAINT uq_user_class_role UNIQUE (user_id, class_id, role_in_class)
);

-- 5. 收集任务
CREATE TABLE essay_tasks (
  id            SERIAL PRIMARY KEY,
  name          VARCHAR(100) UNIQUE NOT NULL,
  grade         VARCHAR(20) NOT NULL,
  essay_number  INTEGER DEFAULT 1,
  essay_topic   VARCHAR(200) DEFAULT '',
  course_id     INTEGER REFERENCES course(id),
  teaching_mode VARCHAR(10) DEFAULT '线下',
  deadline      TIMESTAMP,
  is_active     BOOLEAN DEFAULT FALSE,
  deleted_at    TIMESTAMP,
  created_at    TIMESTAMP DEFAULT now(),
  updated_at    TIMESTAMP DEFAULT now()
);

-- 6. 作文（核心）
CREATE TABLE essays (
  id             SERIAL PRIMARY KEY,
  class_id       INTEGER NOT NULL REFERENCES course(id),
  task_id        INTEGER REFERENCES essay_tasks(id),
  course_id      INTEGER REFERENCES course(id),
  grade          VARCHAR(20) DEFAULT '',
  essay_number   INTEGER DEFAULT 1,
  essay_title    VARCHAR(200) DEFAULT '',
  student_name   VARCHAR(50) NOT NULL,
  is_supplement  BOOLEAN DEFAULT FALSE,
  teaching_mode  VARCHAR(10) DEFAULT '线下',
  remark         TEXT DEFAULT '',
  collector_note TEXT DEFAULT '',
  reviewer_note  TEXT DEFAULT '',
  content_text   TEXT DEFAULT '',
  content_file   VARCHAR(500) DEFAULT '',
  file_type      VARCHAR(10) DEFAULT 'text',
  collected_by   INTEGER NOT NULL REFERENCES users(id),
  status         VARCHAR(20) DEFAULT 'pending',
  file_saved     BOOLEAN DEFAULT TRUE,
  corrected_text TEXT DEFAULT '',
  reviewer_id    INTEGER REFERENCES users(id),
  corrected_at   TIMESTAMP,
  deleted_at     TIMESTAMP,
  created_at     TIMESTAMP DEFAULT now(),
  updated_at     TIMESTAMP DEFAULT now(),
  CONSTRAINT ck_essays_status CHECK (status IN ('pending','confirming','corrected')),
  CONSTRAINT uq_essay_task_student UNIQUE (class_id, task_id, student_name, essay_number, is_supplement, essay_title)
);

CREATE INDEX idx_essays_status        ON essays(status);
CREATE INDEX idx_essays_collected_by  ON essays(collected_by);
CREATE INDEX idx_essays_grade         ON essays(grade);
CREATE INDEX idx_essays_created_at    ON essays(created_at);
CREATE INDEX idx_essays_task_id       ON essays(task_id);
CREATE INDEX idx_essays_deleted_at    ON essays(deleted_at);

-- 7. 作文图片
CREATE TABLE essay_images (
  id          SERIAL PRIMARY KEY,
  essay_id    INTEGER NOT NULL REFERENCES essays(id),
  filename    VARCHAR(200) NOT NULL,
  image_data  BYTEA NOT NULL,
  created_at  TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_essay_images_essay_id ON essay_images(essay_id);

-- 8. 系统配置
CREATE TABLE system_config (
  id           SERIAL PRIMARY KEY,
  config_key   VARCHAR(100) UNIQUE NOT NULL,
  config_value TEXT DEFAULT '{}',
  updated_at   TIMESTAMP DEFAULT now()
);

-- 9. 操作日志
CREATE TABLE operation_logs (
  id         SERIAL PRIMARY KEY,
  essay_id   INTEGER REFERENCES essays(id) ON DELETE SET NULL,
  user_id    INTEGER NOT NULL REFERENCES users(id),
  action     VARCHAR(20) NOT NULL,
  old_value  TEXT DEFAULT '',
  new_value  TEXT DEFAULT '',
  detail     VARCHAR(500) DEFAULT '',
  batch_id   VARCHAR(50),
  essay_ids  TEXT,
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_operation_logs_essay_id   ON operation_logs(essay_id);
CREATE INDEX idx_operation_logs_created_at ON operation_logs(created_at);
CREATE INDEX idx_operation_logs_user_id    ON operation_logs(user_id);
CREATE INDEX idx_operation_logs_batch_id   ON operation_logs(batch_id);
```

---

## 四、设计说明与已知风险

1. **软删除约定**：`deleted_at` 非空即删除，业务查询均需加 `deleted_at IS NULL` 过滤。
2. **多角色存储**：`users.role` 用逗号分隔字符串（如 `"collector,reviewer"`），非正规化设计，查询需 `LIKE '%collector%'`。
3. **课程表重构（过渡期）**：原 `Class` 已重构为 `Course`（表 `course`）。当前 `essays.class_id` 与 `essays.course_id` **两列均指向 `course.id`**，且 `class_id` 仍为 NOT NULL —— 语义上"班级"与"课程"暂未彻底分离。建议后续明确：
   - 方案 A：合并两列为单一 `course_id`，`essays` 仅按课程归属；
   - 方案 B：若确有"班级"实体，再单独建 `classes` 表，`essays.class_id` 指向它。
   - `essays.course_id` 暂无索引，若频繁按课程筛选/报表建议补 `idx_essays_course_id`。
4. **`user_classes` 半启用**：后端接口存在，前端无调用；`get_collector_classes()`（essays.py:229）零调用，数据可见性未生效。表结构保留，用途为"收集者绑定课程"。
5. **无独立学生表**：`essays.student_name` 仅为字符串，无法跨任务归集学生、维护名单、看成长轨迹（对应需求 R5，暂缓）。
6. **图片存数据库**：`essay_images.image_data` 为 BYTEA，量大时 DB 膨胀、备份慢（对应性能问题 P3）。
7. **密码哈希**：SHA-256 + 硬编码盐，安全性不足，依赖中已有 bcrypt 未启用（对应安全 S2）。
8. **API Key 明文**：`system_config.config_value` 明文存储 OCR/LLM 密钥（对应安全 S6）。
9. **唯一约束过严**：`uq_essay_task_student` 六字段组合唯一，批量导入易冲突（对应 D4）。
10. **无版本化迁移**：仅 `create_all` + 手写 ALTER 补列，无 Alembic（对应 D1）。
11. **管理员定义**：`admin` 角色用户为超级管理员，前端路由与后端 `require_admin` 均按 `role` 包含 `admin` 判断。

## 五、环境配置说明

- 数据库连接：`backend/settings.json` 中 `database` 段，或环境变量 `ESSAY_DB_HOST/PORT/USER/PASS/NAME`（`backend/app/database.py`）
- 本地开发存在 SQLite 文件 `backend/essay_system.db`（历史遗留），生产使用 PostgreSQL
