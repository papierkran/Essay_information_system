from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, SessionLocal
from .models.models import Essay
from .utils.file_utils import get_upload_dir
from .api import auth, admin, essays
import os

app = FastAPI(title="作文批改收集信息系统", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(essays.router)


@app.on_event("startup")
def on_startup():
    init_db()
    # 启动时清理文件不存在的记录
    db = SessionLocal()
    try:
        essays = db.query(Essay).all()
        for e in essays:
            if e.content_file:
                full = os.path.join(get_upload_dir(), e.content_file)
                if not os.path.exists(full):
                    db.delete(e)
        db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}
