from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, SessionLocal
from .models.models import Essay, OperationLog
from .utils.file_utils import get_upload_dir
from .api import auth, admin, essays
import os

app = FastAPI(title="作文修改收集信息系统", version="0.1.0")


def _cors_config():
    """CORS 配置。
    - 显式设置 ESSAY_CORS_ORIGINS（逗号分隔）时，严格使用白名单。
    - 开发/局域网（ESSAY_ENV != production）未配置时，放行任意来源。
    - 生产环境（ESSAY_ENV=production）必须配置白名单，否则拒绝跨域。
    """
    origins = [o.strip().rstrip("/") for o in os.environ.get("ESSAY_CORS_ORIGINS", "").split(",") if o.strip()]
    if origins:
        return {"allow_origins": origins, "allow_origin_regex": None}
    env = os.environ.get("ESSAY_ENV", "development")
    if env == "production":
        return {"allow_origins": [], "allow_origin_regex": None}
    return {"allow_origins": [], "allow_origin_regex": ".*"}


_cors = _cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors["allow_origins"],
    allow_origin_regex=_cors["allow_origin_regex"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(essays.router)


if os.environ.get("ESSAY_ENV", "development") == "production":
    _scheme = os.environ.get("ESSAY_TLS", "https")
    if _scheme != "https":
        print("警告: 生产环境建议通过反向代理强制 HTTPS（ESSAY_TLS=https），避免登录口令明文传输")
    if not _cors["allow_origins"]:
        print("警告: 生产环境未设置 ESSAY_CORS_ORIGINS，跨域请求将被拒绝，请配置前端来源白名单")


@app.on_event("startup")
def on_startup():
    init_db()
    # 启动时同步 file_saved 状态（仅标记，不删除记录）
    db = SessionLocal()
    try:
        essays = db.query(Essay).all()
        for e in essays:
            if e.content_file:
                full = os.path.join(get_upload_dir(), e.content_file)
                e.file_saved = os.path.exists(full)
            else:
                e.file_saved = True
        db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}
