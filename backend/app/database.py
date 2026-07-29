import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")


def _load_db_settings():
    """从 settings.json 读取数据库连接配置，环境变量优先。"""
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                settings = json.load(f)
        except Exception:
            pass

    db = settings.get("database", {})
    return {
        "host": os.environ.get("ESSAY_DB_HOST", db.get("host", "")),
        "port": os.environ.get("ESSAY_DB_PORT", db.get("port", "5432")),
        "user": os.environ.get("ESSAY_DB_USER", db.get("user", "")),
        "password": os.environ.get("ESSAY_DB_PASS", db.get("password", "")),
        "database": os.environ.get("ESSAY_DB_NAME", db.get("database", "")),
        "docker_container": os.environ.get("ESSAY_DOCKER_CONTAINER", db.get("docker_container", "pg")),
    }


def _build_database_url(cfg):
    host = cfg["host"]
    port = cfg["port"]
    user = cfg["user"]
    password = cfg["password"]
    database = cfg["database"]
    if not host:
        raise RuntimeError(
            "数据库连接未配置，请通过系统设置页或环境变量 ESSAY_DB_HOST 配置"
        )
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


DB_CONFIG = _load_db_settings()
DATABASE_URL = _build_database_url(DB_CONFIG)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=60)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
