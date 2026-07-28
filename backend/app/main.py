from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, SessionLocal
from .models.models import Essay, OperationLog
from .utils.file_utils import get_upload_dir
from .api import auth, admin, essays
import os

app = FastAPI(title="作文修改收集信息系统", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(essays.router)


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
