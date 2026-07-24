from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import json
from datetime import datetime

from ..database import get_db
from ..models.models import User, Organization, Class, UserClass, Essay
from ..schemas.schemas import (
    UserCreate, UserOut, OrganizationCreate, OrganizationOut,
    ClassCreate, ClassOut
)
from ..utils.auth import hash_password, get_current_user

router = APIRouter(prefix="/api/admin", tags=["管理员"])


def require_admin(user: User):
    if "admin" not in user.role:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ===== 培训班管理 =====
@router.post("/organizations", response_model=OrganizationOut)
def create_org(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    org = Organization(name=data.name, desc=data.desc)
    db.add(org)
    db.commit()
    db.refresh(org)
    return OrganizationOut.model_validate(org)


@router.get("/organizations", response_model=list[OrganizationOut])
def list_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    orgs = db.query(Organization).all()
    return [OrganizationOut.model_validate(o) for o in orgs]


@router.put("/organizations/{org_id}", response_model=OrganizationOut)
def update_org(
    org_id: int,
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="培训班不存在")
    org.name = data.name
    org.desc = data.desc
    db.commit()
    db.refresh(org)
    return OrganizationOut.model_validate(org)


@router.delete("/organizations/{org_id}")
def delete_org(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="培训班不存在")
    db.delete(org)
    db.commit()
    return {"message": "删除成功"}


# ===== 班级管理 =====
@router.post("/classes", response_model=ClassOut)
def create_class(
    data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    cls = Class(org_id=data.org_id, name=data.name)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return ClassOut.model_validate(cls)


@router.get("/classes", response_model=list[ClassOut])
def list_classes(
    org_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    q = db.query(Class)
    if org_id:
        q = q.filter(Class.org_id == org_id)
    classes = q.all()
    return [ClassOut.model_validate(c) for c in classes]


@router.put("/classes/{class_id}", response_model=ClassOut)
def update_class(
    class_id: int,
    data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    cls.name = data.name
    cls.org_id = data.org_id
    db.commit()
    db.refresh(cls)
    return ClassOut.model_validate(cls)


@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    db.delete(cls)
    db.commit()
    return {"message": "删除成功"}


@router.post("/import-classes-csv/preview")
async def preview_classes_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """预览 ClassIn CSV 中的班级列表"""
    require_admin(current_user)
    content = await file.read()
    if content[:2] == b'\xff\xfe':
        text = content.decode("utf-16-le")
    elif content[:2] == b'\xfe\xff':
        text = content.decode("utf-16-be")
    else:
        text = content.decode("utf-8", errors="replace")
    text = text.lstrip("\ufeff").strip()
    lines = text.split("\n")

    classes_list = []
    seen = set()
    for line in lines:
        line = line.strip()
        if not line or 'ClassIn' in line or '学校名称' in line or '时间:' in line or '班级ID' in line:
            continue
        cols = line.split(',')
        if len(cols) < 3:
            continue
        name = cols[1].strip().strip('"')
        if not name or name in ('--', '-') or name in seen:
            continue
        seen.add(name)
        # 检查是否已存在
        existing = db.query(Class).filter(Class.name == name).first()
        classes_list.append({"name": name, "exists": existing is not None})

    return {"classes": classes_list}


@router.post("/import-classes-csv/confirm")
async def confirm_import_classes(
    file: UploadFile = File(...),
    selected: str = Form("[]"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认导入选中的班级"""
    require_admin(current_user)
    import json
    selected_names = json.loads(selected) if isinstance(selected, str) else selected
    content = await file.read()
    if content[:2] == b'\xff\xfe':
        text = content.decode("utf-16-le")
    elif content[:2] == b'\xfe\xff':
        text = content.decode("utf-16-be")
    else:
        text = content.decode("utf-8", errors="replace")

    # 找已存在的org
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="尹老师文科工作室")
        db.add(org)
        db.commit()
        db.refresh(org)

    imported = 0
    skipped = 0
    for name in selected_names:
        existing = db.query(Class).filter(
            Class.org_id == org.id,
            Class.name == name,
        ).first()
        if existing:
            skipped += 1
            continue
        cls = Class(org_id=org.id, name=name)
        db.add(cls)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped}


# ===== 用户管理 =====
@router.post("/users", response_model=UserOut)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname,
        phone=data.phone,
        role=data.role,
        org_id=data.org_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    users = db.query(User).all()
    return [UserOut.model_validate(u) for u in users]


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.nickname is not None:
        user.nickname = data.nickname
    if data.phone is not None:
        user.phone = data.phone
    if data.role:
        user.role = data.role
    if data.password:
        user.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 将该用户的作文 collected_by 置为 1（管理员 ID）
    db.query(Essay).filter(Essay.collected_by == user_id).update({"collected_by": 1})
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


@router.put("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = role
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/profile/password")
def update_my_password(
    old_password: str = "",
    new_password: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户自己修改密码"""
    from ..utils.auth import verify_password, hash_password
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if not new_password or len(new_password) < 4:
        raise HTTPException(status_code=400, detail="新密码至少4位")
    current_user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "密码修改成功"}


# ===== 班级收集者配置 =====
@router.post("/classes/{class_id}/collectors")
def set_class_collectors(
    class_id: int,
    user_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    # 清除旧的收集者
    db.query(UserClass).filter(
        UserClass.class_id == class_id,
        UserClass.role_in_class == "collector",
    ).delete()
    # 添加新收集者
    for uid in user_ids:
        db.add(UserClass(user_id=uid, class_id=class_id, role_in_class="collector"))
    db.commit()
    return {"message": "ok"}


@router.get("/classes/{class_id}/collectors", response_model=list[UserOut])
def get_class_collectors(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    ucs = db.query(UserClass).filter(
        UserClass.class_id == class_id,
        UserClass.role_in_class == "collector",
    ).all()
    users = [uc.user for uc in ucs if uc.user]
    return [UserOut.model_validate(u) for u in users]


# ===== 系统设置 =====
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "settings.json")

@router.get("/settings")
def get_settings(current_user: User = Depends(get_current_user)):
    require_admin(current_user)
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
    else:
        settings = {"upload_dir": "uploads"}

    # 获取真实解析路径
    from ..utils.file_utils import get_upload_dir
    settings["_resolved_path"] = os.path.abspath(get_upload_dir())
    return settings


@router.put("/settings")
def update_settings(data: dict, current_user: User = Depends(get_current_user)):
    require_admin(current_user)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)
    return data


@router.get("/database/export")
def export_database(current_user: User = Depends(get_current_user)):
    """导出数据库为 SQL 文件"""
    require_admin(current_user)
    import subprocess, tempfile
    from ..database import DB_CONFIG
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode="w")
    tmp_path = tmp.name
    tmp.close()
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    # 使用远程容器内的 pg_dump（保证版本匹配）
    result = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "root@" + DB_CONFIG["host"],
         "docker", "exec", "pg", "pg_dump", "-U", DB_CONFIG["user"], "-d", DB_CONFIG["database"],
         "--no-owner", "--no-acl"],
        env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"导出失败: {result.stderr}")
    with open(tmp_path, "w") as f:
        f.write(result.stdout)
    return FileResponse(tmp_path, filename=f"essay_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql", media_type="application/octet-stream")


@router.post("/database/import")
async def import_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """导入 SQL 文件恢复数据库"""
    require_admin(current_user)
    import subprocess, tempfile
    from ..database import DB_CONFIG
    content = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode="wb")
    tmp.write(content)
    tmp_path = tmp.name
    tmp.close()
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    # 通过 SSH 将 SQL 文件传到远程后导入
    remote_path = "/tmp/essay_import.sql"
    sp_run = subprocess.run
    # 上传文件
    sp_run(["scp", "-o", "StrictHostKeyChecking=no", tmp_path, f"root@{DB_CONFIG['host']}:{remote_path}"],
           capture_output=True)
    # 在容器中执行导入
    result = sp_run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "root@" + DB_CONFIG["host"],
         "docker", "exec", "-i", "pg", "psql", "-U", DB_CONFIG["user"], "-d", DB_CONFIG["database"], "-f", remote_path],
        capture_output=True, text=True
    )
    os.unlink(tmp_path)
    # 清理远程临时文件
    sp_run(["ssh", "-o", "StrictHostKeyChecking=no", "root@" + DB_CONFIG["host"], "rm", "-f", remote_path], capture_output=True)
    if result.returncode != 0 and "ERROR" in result.stderr:
        raise HTTPException(status_code=500, detail=f"导入失败: {result.stderr[:300]}")
    return {"message": "导入成功"}
