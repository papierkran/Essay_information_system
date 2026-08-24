# 作文收集与批改管理系统 (Essay Information System)

面向培训机构的作文收集与批改管理平台，支持桌面端和手机端双端适配。提供作文上传、OCR 识别、AI 错别字修正、AI 改写、批量流水线、多角色权限控制、统计分析、docx 导出等功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vant 4 + Vite + ECharts |
| 后端 | FastAPI + SQLAlchemy 2.0 + PostgreSQL |
| 外部服务 | 讯飞 OCR、DeepSeek/OpenAI API（可配置） |

## 快速开始

### 先决条件

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- 推荐：Linux 系统部署

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置数据库连接和 JWT 密钥
python run.py
```

默认监听 `0.0.0.0:6886`。

### 前端

```bash
cd frontend
npm install
npm run dev          # 开发模式，默认 5173
npm run build        # 生产构建，输出 dist/
```

### 构建后部署

构建产物 `dist/` 部署到 Nginx，配置 `/api` 反向代理到后端 `http://localhost:6886`。

## 项目结构

```
Essay_information_system/
├── backend/
│   ├── app/
│   │   ├── api/           # 路由：auth.py, admin.py, essays.py
│   │   ├── models/        # SQLAlchemy ORM 模型
│   │   ├── schemas/       # Pydantic 校验模型
│   │   ├── services/      # 后台任务管理（线程池并行）
│   │   ├── utils/         # auth, crypto_utils, file_utils, ocr_utils
│   │   ├── database.py    # 数据库连接配置
│   │   └── main.py        # FastAPI 入口
│   ├── uploads/           # 上传文件默认目录
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/         # 13 个页面组件
│   │   ├── api/           # Axios 实例与拦截器（多账号切换）
│   │   ├── router/        # 路由与权限守卫
│   │   └── composables/   # 通用组合式函数
│   └── vite.config.js
├── .env.example
├── sql.md                 # 数据库设计文档
└── README.md
```

## 角色权限

| 角色 | 权限 |
|------|------|
| **admin** | 全部权限。用户管理、班级/任务管理、系统设置、备份/恢复 |
| **collector** | 上传/编辑/删除作文，OCR 识别，AI 错别字修正 |
| **reviewer** | 批改/认领/确认/退回，AI 改写，导出 docx |
| **guest** | 只读查看（列表/详情/统计），不可下载、导出、上传、编辑 |

支持多角色共存（如 `collector,reviewer`）。

## 核心功能

### 作文管理
- 单篇/批量上传（图片 / docx / 粘贴文本）
- 文件按序重命名，支持更新已有作文
- 作文状态流转：`pending` → `confirming` → `corrected`，支持退回重改（`rework`）

### OCR 识别
- 对接讯飞 OCR API，自动识别图片文字
- 图片自动矫正（纠正倾斜/旋转）
- 支持单篇 OCR 和批量 OCR

### AI 处理
- **错别字修正**：基于 LLM 修正错别字和识别错误，同时提取标题/作者/年级等元数据
- **AI 改写**：基于 LLM 对作文进行润色改写，支持字数范围控制
- **批量流水线**：OCR → 错别字修正 → 改写，三阶段串联，线程池并行，进度可视

### 导出
- **docx 导出**：宋体小四 12pt，行距最小值 12 磅，首行缩进 0.74cm
- 文件名格式：`改_{标题}——{学生}第{N}次{线上/线下}{补交}.docx`
- 支持批量 zip 导出，CSV 导出
- 下载原文/导出修改前后均从数据库生成 docx

### 数据统计
- 概览卡片（总数/待处理/已修改/本月新增）
- 近 N 天趋势图（7/14/30/90 天可切换）
- GitHub 风格上传频率热力图（支持年/日期范围筛选）
- 状态分布、年级分布、课程分布、收集者排行
- 每月上传/修改柱状图

### 系统设置
- 数据库连接配置（支持 Docker / 本地 PostgreSQL）
- 后端服务地址配置
- 上传存储目录配置（含文件迁移）
- OCR / AI 错别字修正 / AI 改作文配置（API 地址、密钥、模型、提示词）
- 数据库备份（手动触发 + 定时频率 + 备份文件列表管理）

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ESSAY_ENV` | 运行环境 | `development` |
| `ESSAY_JWT_SECRET` | JWT 签名密钥 | 生产环境必填 |
| `ESSAY_CORS_ORIGINS` | CORS 白名单（逗号分隔） | 生产环境必填 |
| `ESSAY_CRYPTO_SECRET` | API 密钥加密密钥 | 可选 |
| `ESSAY_UPLOAD_DIR` | 文件存储目录 | `uploads` |
| `ESSAY_DB_HOST` | 数据库地址 | 通过 settings.json 配置 |
| `ESSAY_DB_PORT` | 数据库端口 | 通过 settings.json 配置 |
| `ESSAY_DB_USER` | 数据库用户 | 通过 settings.json 配置 |
| `ESSAY_DB_PASS` | 数据库密码 | 通过 settings.json 配置 |
| `ESSAY_DB_NAME` | 数据库名 | 通过 settings.json 配置 |

### settings.json

运行后自动生成 `backend/app/settings.json`，存储数据库连接信息和上传目录配置，也可通过系统设置页面修改。

## 部署建议

### 服务器配置

| 用户规模 | 推荐配置 |
|----------|----------|
| 2-3 人测试 | 1 核 1GB 内存 20GB 磁盘 |
| 10 人日常 | 2 核 2GB 内存 40GB 磁盘 + 5Mbps 带宽 |

### 生产部署

```bash
# 后端：多进程启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 6886 --workers 2

# 前端：构建后通过 Nginx 反代
npm run build
# 将 dist/ 部署到 Nginx，配置 /api 反代到后端
```

### 注意事项
- 生产环境必须设置 `ESSAY_JWT_SECRET` 和 `ESSAY_CORS_ORIGINS`
- 使用 Nginx 反向代理并配置 HTTPS
- 配置数据库定期备份策略
- 上传目录放在持久化存储，设置合理权限

## 依赖

### Python（requirements.txt）

```
fastapi, uvicorn, sqlalchemy, python-jose, passlib, python-multipart,
aiofiles, openai, httpx, python-docx, psycopg2-binary, opencv-python-headless
```

### Node（package.json）

```
vue 3, vant 4, axios, vue-router, pinia, echarts, vue-echarts, jszip
```

## 数据库

详细数据库设计见 `sql.md`，包含所有表结构、字段说明、索引和约束。后端使用 SQLAlchemy ORM，启动时自动创建表。

## 许可证

本项目采用仓库根目录 LICENSE 文件中声明的许可证。