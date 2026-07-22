import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# PostgreSQL 连接（优先使用环境变量）
DB_HOST = os.environ.get("ESSAY_DB_HOST", "192.168.31.245")
DB_PORT = os.environ.get("ESSAY_DB_PORT", "5432")
DB_USER = os.environ.get("ESSAY_DB_USER", "postgres")
DB_PASS = os.environ.get("ESSAY_DB_PASS", "040311")
DB_NAME = os.environ.get("ESSAY_DB_NAME", "essay_system")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=60)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 导出配置给其他模块（如数据库导出）
DB_CONFIG = {"host": DB_HOST, "port": DB_PORT, "user": DB_USER, "password": DB_PASS, "database": DB_NAME}


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
