# 📖 作文收集管理系统

面向培训机构的作文收集与批改管理平台，支持桌面端和手机端双端适配。

## 功能概览

| 模块 | 功能 |
|------|------|
| 📤 作文上传 | 单个/批量上传，支持多图片、docx、文字粘贴，图片按序重命名，支持更新已有作文 |
| 📝 批量上传 | 按文件夹结构批量上传作文，批量上传批改结果（自动解析 docx 修改前/后文字） |
| 📋 作文列表 | 多条件筛选（状态/课程/任务/学生/字数/时间等）、多列排序、分页、批量删除/导出/更换收集者/更换任务 |
| ✏️ 作文详情 | 修改前/后分栏、字数统计、全屏模式、段落渲染、重新上传、图片预览、OCR 识别、AI 错别字修正、AI 一键修改 |
| 📝 批改管理 | 待批列表、认领批改、文件+文字批改（corrected_text 入库）、确认修改、标记待重改（rework） |
| 🔄 待重改 | 批改待确认后可标记重改，重新修改后再确认 |
| 🤖 AI 能力 | OCR 识别（讯飞）、AI 错别字修正、AI 改写；批量流水线（OCR→错别字→一键修改）多线程执行、进度可视 |
| 📥 下载导出 | 下载原文、导出修改前后 docx（宋体小四规范格式）、批量导出 zip、合并导出 docx、按课程导出、导出 CSV |
| 📊 工作台 | 快捷入口、活跃收集任务（含实时统计与截止提醒）、最近上传 |
| 👥 用户管理 | 4 角色（管理员/收集者/批改者/游客），多角色支持，多账号共存登录 |
| 📚 课程管理 | 课程 CRUD + CSV 批量导入（预览勾选） |
| 📋 任务管理 | 收集任务 CRUD，关联课程，激活/停用 |
| ⚙️ 系统设置 | 上传目录配置（自动迁移文件）、数据库连接、数据库备份/导入、OCR/LLM 配置（密钥加密存储） |
| 📋 操作日志 | 全部操作记录（上传/认领/批改/编辑/删除/恢复/OCR），支持撤销恢复 |

## 作文状态流转

```
pending（未修改） ──认领/批改──▶ confirming（待确认） ──确认──▶ corrected（已修改）
                                   │
                                   └──标记重改──▶ rework（待重改）──重新批改──▶ confirming
```

- `AI 一键修改` 完成后自动置为 `confirming`
- `rework`（待重改）为待确认作文可退回重改的状态

## 技术栈

| 层 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite 8 + Vant 4 + Axios + JSZip |
| 后端 | Python 3.10+ + FastAPI + SQLAlchemy + PostgreSQL |
| 认证 | JWT (python-jose) + **bcrypt**，30 天有效期 |
| 安全 | CORS 白名单、生产强制 JWT 密钥、API 密钥 Fernet 加密（cryptography） |
| 文件 | python-docx（文字转 docx，宋体小四规范格式） |
| 批改并发 | ThreadPoolExecutor 多线程批量 OCR/LLM 任务 |
| 部署 | Nginx 反向代理 + PostgreSQL |

## 快速启动

### 1. 环境准备

```bash
# Python 3.10+，Node.js 18+
pip install -r backend/requirements.txt
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env 修改 JWT 密钥、运行环境、数据库连接、存储目录、CORS 白名单
```

### 3. 启动后端

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 6886
```

### 4. 启动前端（开发模式）

```bash
cd frontend
npm install
npm run dev
```

### 5. 构建前端（生产部署）

```bash
cd frontend
npm run build
# 把 dist/ 部署到 nginx
```

### 6. 访问

- 开发模式：`http://localhost:5173`
- 生产模式：`https://your-domain`
- 默认管理员：`admin` / `admin`

## 项目结构

```
Essay_information_system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # 认证接口（注册/登录/获取用户信息）
│   │   │   ├── admin.py         # 管理接口（用户/课程/任务/设置/备份/CSV导入）
│   │   │   └── essays.py        # 作文接口（上传/列表/详情/批改/下载/导出/批量任务/操作日志）
│   │   ├── models/
│   │   │   └── models.py        # SQLAlchemy ORM 模型（users/course/essay_tasks/essays/...）
│   │   ├── schemas/
│   │   │   └── schemas.py       # Pydantic 数据模型
│   │   ├── services/
│   │   │   └── task_manager.py  # 批量任务管理（多线程 OCR/LLM，进度跟踪）
│   │   ├── utils/
│   │   │   ├── auth.py          # JWT 认证工具（bcrypt 密码哈希）
│   │   │   ├── crypto_utils.py  # API 密钥 Fernet 加密/解密
│   │   │   ├── file_utils.py    # 文件路径/命名工具（含路径穿越防护）
│   │   │   └── ocr_utils.py     # OCR（讯飞）/ AI 错别字修正 / AI 改写
│   │   ├── database.py          # SQLAlchemy 引擎 + 轻量迁移
│   │   └── main.py              # FastAPI 入口（CORS 白名单、启动同步）
│   ├── uploads/                 # 作文文件存储（默认）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面组件（12 个页面）
│   │   ├── components/
│   │   │   └── TaskStatusBar.vue # 批量任务进度条
│   │   ├── composables/
│   │   │   ├── useScreen.js     # 响应式断点 composable
│   │   │   └── useTaskMonitor.js # 批量任务轮询
│   │   ├── api/
│   │   │   └── index.js         # Axios 实例 + 多账号认证 + 拦截器
│   │   ├── router/
│   │   │   └── index.js         # 路由配置（含角色权限守卫）
│   │   ├── utils/
│   │   │   └── format.js        # 日期格式化工具
│   │   ├── App.vue              # 根组件（侧边栏导航）
│   │   └── main.js              # 入口
│   ├── vite.config.js           # Vite 配置（API 代理、后端地址）
│   └── package.json
├── $MMM $DD.docx                # 作文模板（含"修改前：""修改后："分页结构）
├── .env.example                 # 环境变量示例
├── sql.md                       # 数据库设计文档
├── todo.md                      # 需求调研与改进清单
└── README.md
```

## 角色权限

| 角色 | 可操作 |
|------|--------|
| **管理员** | 全部权限（用户/课程/任务/作文管理、系统设置、数据库备份、批量操作） |
| **收集者** | 上传作文（单个+批量）、查看作文列表、编辑/删除自己的作文 |
| **批改者** | 查看待批列表、认领批改、上传批改结果（文件+文字）、确认/标记重改、查看操作日志 |
| **游客** | 只读查看（作文列表、待批列表、详情、操作日志），不可下载/导出/编辑 |

- 一人可多角色（如 `"collector,reviewer"`）
- `admin` 用户为超级管理员，不可被其他管理员编辑/删除
- 注册接口仅允许注册 `collector` 角色，管理员账号由管理员创建
- 游客看到的操作按钮均为「仅查看」

## 导出 docx 格式规范

| 属性 | 值 |
|------|-----|
| 字体 | 宋体（含东亚字体） |
| 字号 | 小四 = 12pt |
| 行距 | 最小值 12 磅 |
| 首行缩进 | 0.74cm |
| 段前/段后 | 0 |
| 标题行（前 2 段） | 居中 + 加粗 |
| 文件名 | `改_{标题}——{学生}第{N}次{线上/线下}{补交}.docx` |

## 存储目录结构

```
{upload_dir}/
  {年份}/
    {MMDD}_{课程名}/           # 有关联任务时
      {年级}{线上/线下}第{N}次/
        {学生姓名}/
          1.jpg
          2.jpg
          {标题}_{姓名}_{次数}_{补交}_{备注}_{时间戳}.docx
          改_{原文件名}.docx
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ESSAY_ENV` | 运行环境 `development`/`production`；production 强制要求 JWT 密钥与 CORS 白名单 | `development` |
| `ESSAY_JWT_SECRET` | JWT 签名密钥（production 必须设置，否则拒绝启动） | 开发用默认密钥 |
| `ESSAY_CORS_ORIGINS` | CORS 白名单（逗号分隔完整来源）；production 未配置则拒绝跨域 | 空 |
| `ESSAY_CRYPTO_SECRET` | API 密钥加密密钥（可选，未设置回退到 ESSAY_JWT_SECRET） | 空 |
| `ESSAY_UPLOAD_DIR` | 上传文件存储目录 | `uploads` |
| `ESSAY_DB_HOST` | 数据库主机 | settings.json 配置 |
| `ESSAY_DB_PORT` | 数据库端口 | `5432` |
| `ESSAY_DB_USER` | 数据库用户 | settings.json 配置 |
| `ESSAY_DB_PASS` | 数据库密码 | settings.json 配置 |
| `ESSAY_DB_NAME` | 数据库名 | settings.json 配置 |

## API 后端地址配置

前端支持两种方式配置后端地址：

1. **Nginx 代理**（推荐）：前端 `/api` 由 nginx 转发到后端，无需额外配置
2. **手动设置**：登录页 ⚙️ 设置服务器地址，或管理后台系统设置中配置

`vite.config.js` 中可通过 `define.__API_BASE_URL__` 在构建时写死后端地址。
