import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.models import User

_DEV_SECRET = "essay-system-dev-secret-change-in-production"
_env_secret = os.environ.get("ESSAY_JWT_SECRET", "")


def _resolve_secret_key() -> str:
    """强制生产环境配置 JWT 密钥，禁止回退到硬编码密钥。"""
    if _env_secret:
        return _env_secret
    env = os.environ.get("ESSAY_ENV", "development")
    if env == "production":
        raise RuntimeError("生产环境必须设置环境变量 ESSAY_JWT_SECRET")
    return _DEV_SECRET


SECRET_KEY = _resolve_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = None  # 保留占位，实际使用 bcrypt 库

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if hashed_password.startswith("$2"):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except (ValueError, TypeError):
            return False
    legacy = hashlib.sha256(('essay_salt_' + plain_password).encode()).hexdigest()
    return legacy == hashed_password


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的令牌")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return user
