# 📖 作文收集管理系统

面向培训机构的作文收集与批改管理平台，支持双端适配（桌面端 + 手机端）。

## 功能概览

| 功能 | 说明 |
|------|------|
| 📤 作文上传 | 支持多图片、docx、文字粘贴，图片按序重命名 |
| 📋 作文列表 | 多条件筛选 + 排序 + 分页 + 行内编辑 + 批量删除 |
| ✏️ 详情编辑 | 可编辑全部字段，图片预览，重新上传文件 |
| 📝 批改管理 | 待批列表、批改历史、批改文件上传/下载 |
| 📊 工作台 | 快捷入口 + 最近上传 |
| 👥 用户管理 | 多角色（管理员/收集者/批改者），多账号共存登录 |
| 🏫 班级管理 | CSV 导入班级（预览勾选），创建/编辑/删除 |
| ⚙️ 系统设置 | 自定义上传存储目录 |
| 📥 导出 CSV | 当前筛选结果导出为表格文件 |

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Vite + Vant 4 + ECharts + Axios |
| 后端 | Python + FastAPI + SQLAlchemy + SQLite |
| 认证 | JWT (python-jose + passlib) |
| 文件 | python-docx（文字转 docx 模板） |

## 快速启动

### 1. 环境准备

```bash
# Python 3.10+，Node.js 18+
pip install --break-system-packages -r backend/requirements.txt
```

### 2. 配置环境变量（可选）

```bash
cp .env.example .env
# 编辑 .env 修改 JWT 密钥和存储目录
```

### 3. 启动后端

```bash
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 启动前端（开发模式）

```bash
cd frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

### 5. 访问

浏览器打开 `http://localhost:5173`

默认管理员账号：`admin` / `admin`

## 项目结构

```
Essay_information_system/
├── backend/
│   ├── app/
│   │   ├── api/            # 路由（auth, admin, essays）
│   │   ├── models/         # ORM 模型
│   │   ├── schemas/        # Pydantic 数据模型
│   │   ├── utils/          # 工具（auth, file_utils）
│   │   ├── database.py     # SQLAlchemy 引擎
│   │   └── main.py         # FastAPI 入口
│   ├── uploads/            # 作文文件存储
│   ├── essay_system.db     # SQLite 数据库
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── api/            # API 客户端 + 多账号认证
│   │   ├── router/         # 路由配置
│   │   ├── composables/    # 组合式函数
│   │   └── App.vue         # 根组件（含全局样式）
│   ├── vite.config.js
│   └── package.json
├── $MMM $DD.docx           # 作文模板（含分页符）
├── .env.example            # 环境变量示例
└── 作文批改系统计划书.md    # 需求文档
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ESSAY_JWT_SECRET` | JWT 签名密钥 | `essay-…tion`（开发用，生产环境务必修改） |
| `ESSAY_UPLOAD_DIR` | 上传文件存储目录 | `uploads`（相对 backend/） |

## 角色权限

| 角色 | 可操作 |
|------|--------|
| 管理员 | 全部权限（用户/班级/作文管理、系统设置） |
| 收集者 | 上传作文、查看自己收集的列表、详情编辑 |
| 批改者 | 查看待批列表、认领批改、上传批改结果 |

一人可多角色（如既是收集者又是批改者）。

## 存储目录结构

```
{上传目录}/
  {年份}/
    {月}月/
      {日}/
        {年级}{线上/线下}/
          第{次数}次/
            {收集者}/
              {学生姓名}/
                1.jpg
                2.jpg
                {标题}_{姓名}_{次数}_{时间戳}.docx
                改_{原文件名}.docx
```
