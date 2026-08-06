# 数据库设计文档（sql.md）

> 来源：`backend/app/models/models.py`（SQLAlchemy ORM 定义）
> 数据库：**PostgreSQL**（生产） / SQLite（本地可用）
> 说明：本项目使用 `Base.metadata.create_all()` 建表 + 轻量幂等迁移（`database.py`），**无 Alembic 版本化迁移**。
> 更新：2026-08-06 —— 移除 `organizations`/`user_classes` 表、`Course` 简化、`Essay` 删除 `class_id`、状态新增 `rework`。

---

## 一、表结构总览

| 表名 | 中文含义 | 说明 |
|------|---------|------|
| `users` | 用户 | 支持多角色（admin/collector/reviewer，可逗号组合） |
| `course` | 课程 | 机构课程（如「初一语文」） |
| `essay_tasks` | 收集任务 | 一次作文收集活动（年级/第几次/主题/课程/截止） |
| `essays` | 作文 | 核心业务表，含原文/改后/状态/归属 |
| `essay_images` | 作文图片 | 图片二进制存数据库（LargeBinary） |
| `system_config` | 系统配置 | key-value JSON，存 OCR/LLM 配置（敏感字段加密） |
| `operation_logs` | 操作日志 | 审计日志（含批量操作） |

> 已移除的表：`organizations`（机构，单机构场景不再需要）、`user_classes`（用户-课程绑定，未真正投入使用）。

### 关系图（ER）

```
course        1─N essay_tasks  (course_id 课程)
course        1─N essays       (course_id 课程)
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

### 1. `users` — 用户

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 登录名 |
| password_hash | VARCHAR(200) | NOT NULL | 密码哈希（bcrypt，兼容旧 SHA-256 校验） |
| nickname | VARCHAR(50) | 默认 '' | 昵称 |
| phone | VARCHAR(20) | 默认 '' | 电话 |
| role | VARCHAR(50) | 默认 'collector' | 角色：admin/collector/reviewer，多角色逗号分隔（如 "collector,reviewer"），另有 guest（游客） |
| is_active | BOOLEAN | 默认 true | 是否启用（禁用后登录与鉴权被拒） |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

> 注册接口 `/api/auth/register` 仅允许注册 `collector` 角色，管理员账号由管理员创建。

### 2. `course` — 课程

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| name | VARCHAR(100) | NOT NULL | 课程名称（如「初一语文」） |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

> 支持 CSV 批量导入（`/api/admin/import-courses-csv`，预览+确认两段式）。

### 3. `essay_tasks` — 收集任务

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

> `course_name` 为 ORM 计算属性：`course = relationship("Course")` → `self.course.name`，不落库。

### 4. `essays` — 作文（核心表）

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| task_id | INTEGER | FK→essay_tasks.id, 可空 | 关联收集任务 |
| course_id | INTEGER | FK→course.id, 可空 | 关联课程（上传时优先取传入值，否则从任务继承） |
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
| status | VARCHAR(20) | 默认 'pending' | 状态：pending/confirming/corrected/rework |
| file_saved | BOOLEAN | 默认 true | 文件是否存在于磁盘 |
| corrected_text | TEXT | 默认 '' | 修改后文字内容 |
| reviewer_id | INTEGER | FK→users.id, 可空 | 批改者 |
| corrected_at | TIMESTAMP | NULL | 批改完成时间 |
| deleted_at | TIMESTAMP | NULL | 软删除 |
| created_at | TIMESTAMP | 默认 now | 创建时间 |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

**状态流转**：
- `pending` 未修改 → 认领/批改 → `confirming` 待确认 → 确认 `corrected` 已修改
- `confirming` 可标记为 `rework` 待重改（重新修改后再进入 `confirming`）
- AI 一键修改（ai-rewrite）后自动置为 `confirming`

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
- 唯一约束 `uq_essay_task_student`：(task_id, student_name, essay_number, is_supplement, essay_title)
- 检查约束 `ck_essays_status`：`status IN ('pending','confirming','corrected','rework')`
  - 启动迁移 `database.py:_migrate_essays_status_constraint()` 会自动重建该约束以兼容 `rework`

### 5. `essay_images` — 作文图片

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| essay_id | INTEGER | FK→essays.id, NOT NULL, 索引 | 所属作文 |
| filename | VARCHAR(200) | NOT NULL | 文件名 |
| image_data | BYTEA (LargeBinary) | NOT NULL | 图片二进制（⚠ 存 DB，体积膨胀风险） |
| created_at | TIMESTAMP | 默认 now | 创建时间 |

### 6. `system_config` — 系统配置

| 字段 | 类型 | 约束/默认 | 说明 |
|------|------|----------|------|
| id | INTEGER | PK, 自增, 索引 | 主键 |
| config_key | VARCHAR(100) | UNIQUE, NOT NULL | 配置键（如 ocr、llm_typo_fix、llm_editor） |
| config_value | TEXT | 默认 '{}' | 配置值（JSON；敏感字段以 `enc:` 前缀 Fernet 加密） |
| updated_at | TIMESTAMP | 默认 now | 更新时间 |

> 安全：`utils/crypto_utils.py` 对 `api_key`/`secret`/`token` 等敏感键做 Fernet 加密存储（密钥优先级：`ESSAY_CRYPTO_SECRET` > `ESSAY_JWT_SECRET` > 本地 `.crypto.key`）。

### 7. `operation_logs` — 操作日志

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
-- 1. 用户
CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  username      VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(200) NOT NULL,
  nickname      VARCHAR(50) DEFAULT '',
  phone         VARCHAR(20) DEFAULT '',
  role          VARCHAR(50) DEFAULT 'collector',
  is_active     BOOLEAN DEFAULT TRUE,
  deleted_at    TIMESTAMP,
  created_at    TIMESTAMP DEFAULT now(),
  updated_at    TIMESTAMP DEFAULT now()
);

-- 2. 课程
CREATE TABLE course (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(100) NOT NULL,
  deleted_at  TIMESTAMP,
  created_at  TIMESTAMP DEFAULT now(),
  updated_at  TIMESTAMP DEFAULT now()
);

-- 3. 收集任务
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

-- 4. 作文（核心）
CREATE TABLE essays (
  id             SERIAL PRIMARY KEY,
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
  CONSTRAINT ck_essays_status CHECK (status IN ('pending','confirming','corrected','rework')),
  CONSTRAINT uq_essay_task_student UNIQUE (task_id, student_name, essay_number, is_supplement, essay_title)
);

CREATE INDEX idx_essays_status        ON essays(status);
CREATE INDEX idx_essays_collected_by  ON essays(collected_by);
CREATE INDEX idx_essays_grade         ON essays(grade);
CREATE INDEX idx_essays_created_at    ON essays(created_at);
CREATE INDEX idx_essays_task_id       ON essays(task_id);
CREATE INDEX idx_essays_deleted_at    ON essays(deleted_at);

-- 5. 作文图片
CREATE TABLE essay_images (
  id          SERIAL PRIMARY KEY,
  essay_id    INTEGER NOT NULL REFERENCES essays(id),
  filename    VARCHAR(200) NOT NULL,
  image_data  BYTEA NOT NULL,
  created_at  TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_essay_images_essay_id ON essay_images(essay_id);

-- 6. 系统配置
CREATE TABLE system_config (
  id           SERIAL PRIMARY KEY,
  config_key   VARCHAR(100) UNIQUE NOT NULL,
  config_value TEXT DEFAULT '{}',
  updated_at   TIMESTAMP DEFAULT now()
);

-- 7. 操作日志
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
3. **无独立学生表**：`essays.student_name` 仅为字符串，无法跨任务归集学生、维护名单、看成长轨迹（对应需求 R5，暂缓）。
4. **图片存数据库**：`essay_images.image_data` 为 BYTEA，量大时 DB 膨胀、备份慢（对应性能问题 P3）。
5. **唯一约束**：`uq_essay_task_student`（task_id, student_name, essay_number, is_supplement, essay_title），批量导入冲突面较窄。
6. **无版本化迁移**：仅 `create_all` + 幂等 ALTER（operation_logs 补列、essays 状态约束重建），无 Alembic（对应 D1）。存量库若有已删除的 `organizations`/`user_classes` 表不影响运行。
7. **管理员定义**：`admin` 角色用户为超级管理员，前端路由与后端 `require_admin` 均按 `role` 包含 `admin` 判断。

## 五、环境配置说明

- 数据库连接：`backend/settings.json` 中 `database` 段，或环境变量 `ESSAY_DB_HOST/PORT/USER/PASS/NAME`（`backend/app/database.py`）
- 安全相关环境变量（`ESSAY_ENV`、`ESSAY_JWT_SECRET`、`ESSAY_CORS_ORIGINS`、`ESSAY_CRYPTO_SECRET`）见 `.env.example`
- 本地开发存在 SQLite 文件 `backend/essay_system.db`（历史遗留），生产使用 PostgreSQL
