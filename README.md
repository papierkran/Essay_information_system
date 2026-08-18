# 作文收集与批改管理系统 (Essay Information System)

面向培训机构的作文收集与批改管理平台，支持桌面端与手机端双端适配。提供上传/批量上传、OCR 识别、AI 错别字修正、批改流水线、多角色权限、导出 docx/zip/CSV 等功能，便于收集、批改、导出与统计。

主要亮点
- 单文/批量上传（图片/docx/粘贴文本），支持文件按序重命名与更新
- 批量流水线任务：OCR → 错别字修正 → 一键改写（可多线程并行，进度可视）
- 批改流程支持认领、确认、退回重改（rework）
- 导出规范 docx（宋体小四）、批量 zip 导出、CSV 导出
- 角色控制：管理员 / 收集者 / 批改者 / 游客（支持多角色共存）
- 前后端分离：Vue 3 + Vite 前端，FastAPI + SQLAlchemy 后端，PostgreSQL 存储

快速开始（开发环境）
先决条件
- Python 3.10+
- Node.js 18+
- PostgreSQL（或使用已有数据库）
- 推荐：在 Linux/macOS 上以开发用户运行，生产部署使用 Nginx + systemd

1. 克隆仓库
```bash
git clone git@github.com:papierkran/Essay_information_system.git
cd Essay_information_system
```

2. 后端：安装依赖并运行
```bash
# 进入后端目录
cd backend

# 安装 Python 依赖（推荐在虚拟环境中）
pip install -r requirements.txt

# 复制示例环境配置并编辑
cp .env.example .env
# 编辑 .env：ESSAY_JWT_SECRET、数据库连接、ESSAY_UPLOAD_DIR、ESSAY_CORS_ORIGINS 等

# 启动开发服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 6886
```

默认后端监听端口：6886（可在 .env 或配置中更改）

3. 前端：安装依赖并运行（开发模式）
```bash
cd frontend
npm install
npm run dev
```

默认 Vite 开发服务器端口通常为 5173。生产构建：
```bash
npm run build
# 将 dist/ 部署到 nginx 或静态主机，并配置 /api 代理到后端
```

4. 访问应用
- 开发模式：前端通常在 http://localhost:5173
- 后端 API 示例：http://localhost:6886/api
- 默认管理员（开发环境示例）：admin / admin（请上线前更改）

项目结构（高层）
Essay_information_system/
- backend/
  - app/
    - api/           # 路由：auth.py, admin.py, essays.py 等
    - models/        # SQLAlchemy ORM 模型
    - schemas/       # Pydantic 校验模型
    - services/      # 任务/批处理管理（ThreadPoolExecutor）
    - utils/         # auth, crypto_utils, file_utils, ocr_utils
    - database.py
    - main.py
  - uploads/         # 上传文件默认目录
  - requirements.txt
- frontend/
  - src/
    - views/         # 页面组件（12 个页面）
    - components/
    - composables/   # useTaskMonitor, useScreen 等
    - api/           # Axios 实例与拦截器（多账号支持）
    - router/        # 路由与权限守卫
    - utils/
  - vite.config.js
  - package.json
- .env.example
- sql.md             # 数据库设计文档
- todo.md            # 需求与改进清单
- LICENSE

核心概念
- 作文状态流转：
  pending（未修改） →（认领/批改）→ confirming（待确认） →（确认）→ corrected（已修改）
  其中：confirming 可被标记为 rework（待重改）并退回重改流程
- 批量流水线：支持多线程执行 OCR（讯飞）与基于 LLM 的错别字修正/改写，任务可查看并行进度

关键环境变量（示例）
- ESSAY_ENV: development / production（production 下强制要求 JWT 与 CORS）
- ESSAY_JWT_SECRET: JWT 签名密钥（production 必填）
- ESSAY_CORS_ORIGINS: CORS 白名单（逗号分隔）
- ESSAY_CRYPTO_SECRET: API 密钥加密密钥（可选）
- ESSAY_UPLOAD_DIR: 文件存储目录（默认 uploads）
- ESSAY_DB_HOST / ESSAY_DB_PORT / ESSAY_DB_USER / ESSAY_DB_PASS / ESSAY_DB_NAME

安全与部署注意
- 生产环境请务必：
  - 设置强随机的 ESSAY_JWT_SECRET 与 ESSAY_CRYPTO_SECRET
  - 限制 ESSAY_CORS_ORIGINS 为可信域名
  - 将上传目录（ESSAY_UPLOAD_DIR）放在受控的持久化存储，并设置合理权限
  - 使用 Nginx 做反向代理并配置 HTTPS
  - 配置数据库备份策略（后端提供备份/导入接口）
- 如果启用第三方 OCR/LLM，请在 .env 中安全保存密钥（后端会对 API 密钥进行 Fernet 加密存储）

导出 docx 规范（用于批量导出）
- 字体：宋体（含东亚字体）
- 字号：小四（12pt）
- 行距：最小值 12 磅
- 首行缩进：0.74cm
- 标题前两段：居中加粗
- 导出文件名示例：改_{标题}——{学生}第{N}次{线上/线下}{补交}.docx

数据库与数据模型
- 项目包含详细数据库设计文档 sql.md（ER 关系、表字段说明、索引与约束），部署前请根据 sql.md 创建或迁移数据库结构
- 后端使用 SQLAlchemy 管理 ORM，项目含轻量数据迁移脚本（参见 backend/app/database.py 与代码注释）

开发与调试提示
- 常见端口：前端（5173），后端（6886）
- 后端日志可在启动输出中查看，OCR/LLM 批量任务会将进度写入任务管理表与操作日志
- 前端开发时可在 vite.config.js 中配置 API 代理：将 /api 转发到后端地址，避免 CORS 干扰

贡献与开发流程
- 建议分支策略：feature/*、fix/*、hotfix/*；通过 Pull Request 进行合并与代码审查
- 本仓库 TODO 与需求记录请参见 todo.md
- 若要贡献：
  - Fork 仓库 → 新建分支 → 提交 PR，描述修改点与复现步骤
  - 如涉及数据库变更，请更新 sql.md 或提交迁移脚本

已知事项与后续计划
- 详细的任务/批量处理调度、更多 AI 提升策略与 UI/UX 优化已记录在 todo.md
- sql.md 包含当前数据库设计，部署或迁移前请阅读并确认索引/约束

许可证
- 本项目采用 LICENSE 文件中声明的许可证（见仓库根目录 LICENSE）

快速参考命令（速查）
- 后端依赖安装：pip install -r backend/requirements.txt
- 启动后端：python -m uvicorn app.main:app --host 0.0.0.0 --port 6886
- 前端开发：cd frontend && npm install && npm run dev
- 前端构建：cd frontend && npm run build

附录
- 仓库内文档：
  - .env.example：示例环境变量
  - sql.md：数据库设计说明
  - todo.md：需求与改进清单
- 如需把 README 按你的偏好再精简或增加“部署示例（systemd / nginx）”、“Docker 容器化示例”或“API 端点文档（按接口列出）”，告诉我你想要的格式与重点，我可以基于代码自动生成更详细的部分。