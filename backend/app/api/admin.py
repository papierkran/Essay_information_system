from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import json
import shutil
from datetime import datetime

from ..database import get_db, SessionLocal
from ..models.models import User, Organization, Class, UserClass, Essay, EssayTask, SystemConfig
from ..schemas.schemas import (
    UserCreate, UserOut, OrganizationCreate, OrganizationOut,
    ClassCreate, ClassOut, TaskCreate, TaskOut, PasswordChange,
    SystemConfigOut, SystemConfigUpdate,
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
    orgs = db.query(Organization).filter(Organization.deleted_at == None).all()
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
    org.deleted_at = datetime.now()
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
    q = db.query(Class).filter(Class.deleted_at == None)
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
    cls.deleted_at = datetime.now()
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
    users = db.query(User).filter(User.deleted_at == None).all()
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
    if user.username == "admin":
        raise HTTPException(status_code=403, detail="超级管理员不可编辑")
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
    if user.username == "admin":
        raise HTTPException(status_code=403, detail="超级管理员不可删除")
    # 将该用户的作文 collected_by 置为 1（管理员 ID）
    db.query(Essay).filter(Essay.collected_by == user_id).update({"collected_by": 1})
    user.deleted_at = datetime.now()
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
    if user.username == "admin":
        raise HTTPException(status_code=403, detail="超级管理员不可修改角色")
    user.role = role
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/profile/password")
def update_my_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户自己修改密码"""
    from ..utils.auth import verify_password, hash_password
    if not data.old_password:
        raise HTTPException(status_code=400, detail="请输入原密码")
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if not data.new_password or len(data.new_password) < 4:
        raise HTTPException(status_code=400, detail="新密码至少4位")
    current_user.password_hash = hash_password(data.new_password)
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
    # 软删除旧的收集者绑定
    db.query(UserClass).filter(
        UserClass.class_id == class_id,
        UserClass.role_in_class == "collector",
        UserClass.deleted_at == None,
    ).update({"deleted_at": datetime.now()})
    # 添加新收集者（先恢复已存在的同用户绑定，再新增）
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
        settings = {"upload_dir": "uploads", "database": {}}

    # 获取真实解析路径
    from ..utils.file_utils import get_upload_dir
    settings["_resolved_path"] = os.path.abspath(get_upload_dir())

    # 返回当前数据库连接信息（隐藏密码）
    from ..database import _load_db_settings
    db_info = _load_db_settings()
    settings["_db_info"] = {
        "host": db_info["host"],
        "port": db_info["port"],
        "user": db_info["user"],
        "database": db_info["database"],
        "docker_container": db_info["docker_container"],
    }

    # 保护：返回时从原始设置中移除数据库密码
    db_config = settings.get("database", {})
    if "password" in db_config and db_config["password"]:
        db_config["password"] = ""  # 不回显密码

    return settings


@router.put("/settings")
def update_settings(data: dict, current_user: User = Depends(get_current_user)):
    require_admin(current_user)

    # 读取旧的 upload_dir
    old_upload_dir = ""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            old_settings = json.load(f)
        old_upload_dir = old_settings.get("upload_dir", "uploads")

    new_upload_dir = data.get("upload_dir", "uploads")

    # 保存新设置
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 清除缓存，让 get_upload_dir 读取新值
    from ..utils import file_utils
    file_utils._SETTINGS = None

    # 如果 upload_dir 变了，移动数据库中有记录的文件
    moved = 0
    if old_upload_dir and new_upload_dir and old_upload_dir != new_upload_dir:
        old_abs = os.path.abspath(old_upload_dir)
        new_abs = os.path.abspath(new_upload_dir)

        if os.path.isdir(old_abs):
            # 获取数据库中所有有 content_file 的作文
            db = SessionLocal()
            try:
                essays = db.query(Essay).filter(Essay.content_file != "", Essay.content_file.isnot(None)).all()
                for e in essays:
                    old_file = os.path.join(old_abs, e.content_file)
                    if os.path.exists(old_file):
                        new_file = os.path.join(new_abs, e.content_file)
                        os.makedirs(os.path.dirname(new_file), exist_ok=True)
                        shutil.move(old_file, new_file)
                        moved += 1
            finally:
                db.close()

    return {"message": "设置已保存", "moved": moved}


def _get_config(db: Session, key: str, default: dict = None) -> dict:
    row = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if row:
        try:
            return json.loads(row.config_value)
        except (json.JSONDecodeError, TypeError):
            return default or {}
    return default or {}


def _set_config(db: Session, key: str, value: dict):
    row = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if row:
        row.config_value = json.dumps(value, ensure_ascii=False)
    else:
        row = SystemConfig(config_key=key, config_value=json.dumps(value, ensure_ascii=False))
        db.add(row)
    db.commit()


@router.get("/config/{config_key}", response_model=SystemConfigOut)
def get_config(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定配置（如 ocr, llm）"""
    require_admin(current_user)
    value = _get_config(db, config_key)
    row = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    return SystemConfigOut(
        config_key=config_key,
        config_value=value,
        updated_at=row.updated_at if row else None,
    )


@router.put("/config/{config_key}", response_model=SystemConfigOut)
def update_config(
    config_key: str,
    data: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新指定配置"""
    require_admin(current_user)
    _set_config(db, config_key, data.config_value)
    row = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    return SystemConfigOut(
        config_key=config_key,
        config_value=_get_config(db, config_key),
        updated_at=row.updated_at if row else None,
    )


@router.get("/database/export")
def export_database(current_user: User = Depends(get_current_user)):
    """导出数据库为 SQL 文件"""
    require_admin(current_user)
    import subprocess, tempfile
    from ..database import _load_db_settings
    DB_CONFIG = _load_db_settings()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode="w")
    tmp_path = tmp.name
    tmp.close()
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    container = DB_CONFIG.get("docker_container", "pg")
    # 使用远程容器内的 pg_dump（保证版本匹配）
    # --no-sync: 避免 \restrict 命令（PG16+，PG18 默认启用但显式指定更安全）
    # --clean: DROP 已有对象后重建（替代 --create，避免事务块冲突）
    # --rows-per-insert=1: 逐行 INSERT（PG14+，跨版本兼容）
    # --no-security-labels: 跳过安全标签（避免跨版本策略冲突）
    # --no-subscriptions: 跳过逻辑订阅对象（避免跨库环境问题）
    result = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", "root@" + DB_CONFIG["host"],
         "docker", "exec", container, "pg_dump", "-U", DB_CONFIG["user"], "-d", DB_CONFIG["database"],
         "--no-owner", "--no-acl", "--no-sync", "--clean",
         "--rows-per-insert=1", "--no-security-labels", "--no-subscriptions"],
        env=env, capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"导出失败: {result.stderr}")
    # 清理可能残留的 \restrict 命令（兼容旧备份文件）
    output = result.stdout
    if output.startswith("\\restrict"):
        output = output[output.index("\n") + 1:]
    with open(tmp_path, "w") as f:
        f.write(output)
    return FileResponse(tmp_path, filename=f"essay_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql", media_type="application/octet-stream")


@router.post("/database/import")
async def import_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """导入 SQL 文件恢复数据库"""
    require_admin(current_user)
    import subprocess, tempfile
    from ..database import _load_db_settings
    DB_CONFIG = _load_db_settings()
    content = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode="wb")
    tmp.write(content)
    tmp_path = tmp.name
    tmp.close()
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    container = DB_CONFIG.get("docker_container", "pg")
    # 通过 SSH 将 SQL 文件传到远程后导入
    remote_path = "/tmp/essay_import.sql"
    sp_run = subprocess.run
    # 上传文件（增加超时）
    sp_run(["scp", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", tmp_path, f"root@{DB_CONFIG['host']}:{remote_path}"],
           capture_output=True, timeout=30)
    # 在容器中执行导入（连接目标库）
    result = sp_run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", "root@" + DB_CONFIG["host"],
         "docker", "exec", "-i", container, "psql", "-U", DB_CONFIG["user"], "-d", DB_CONFIG["database"], "-f", remote_path],
        capture_output=True, text=True, timeout=120
    )
    os.unlink(tmp_path)
    # 清理远程临时文件
    sp_run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", "root@" + DB_CONFIG["host"], "rm", "-f", remote_path], capture_output=True, timeout=10)
    if result.returncode != 0 and "ERROR" in result.stderr:
        raise HTTPException(status_code=500, detail=f"导入失败: {result.stderr[:300]}")
    return {"message": "导入成功"}


@router.get("/test-server")
def test_server():
    """测试后端服务是否正常"""
    return {"status": "ok", "message": "后端服务连接正常"}


@router.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    """测试数据库连接是否正常"""
    try:
        db.execute("SELECT 1")
        return {"status": "ok", "message": "数据库连接正常"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")


# ===== 作文收集任务管理 =====
@router.post("/tasks", response_model=TaskOut)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    existing = db.query(EssayTask).filter(EssayTask.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="任务名称已存在")
    task = EssayTask(
        name=data.name,
        grade=data.grade,
        essay_number=data.essay_number or 0,
        essay_topic=data.essay_topic,
        course_name=data.course_name,
        teaching_mode=data.teaching_mode,
        deadline=data.deadline,
        is_active=data.is_active,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    tasks = db.query(EssayTask).filter(EssayTask.deleted_at == None).order_by(EssayTask.created_at.desc()).all()
    # 统计每个任务下已提交的作文数量
    from sqlalchemy import func
    counts = dict(
        db.query(Essay.task_id, func.count(Essay.id))
        .filter(Essay.task_id.isnot(None), Essay.deleted_at == None)
        .group_by(Essay.task_id)
        .all()
    )
    result = []
    for t in tasks:
        out = TaskOut.model_validate(t)
        out.submitted_count = counts.get(t.id, 0)
        result.append(out)
    return result


@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    task = db.query(EssayTask).filter(EssayTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    dup = db.query(EssayTask).filter(
        EssayTask.name == data.name,
        EssayTask.id != task_id
    ).first()
    if dup:
        raise HTTPException(status_code=400, detail="任务名称已存在")
    task.name = data.name
    task.grade = data.grade
    task.essay_number = data.essay_number or 0
    task.essay_topic = data.essay_topic
    task.course_name = data.course_name
    task.teaching_mode = data.teaching_mode
    task.deadline = data.deadline
    task.is_active = data.is_active
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    task = db.query(EssayTask).filter(EssayTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.deleted_at = datetime.now()
    db.commit()
    return {"message": "删除成功"}


@router.put("/tasks/{task_id}/activate")
def activate_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """切换指定任务的活跃状态"""
    require_admin(current_user)
    task = db.query(EssayTask).filter(EssayTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.is_active = not task.is_active
    db.commit()
    return {"message": "已激活" if task.is_active else "已结束", "is_active": task.is_active}


@router.put("/tasks/deactivate-all")
def deactivate_all_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消所有活跃任务"""
    require_admin(current_user)
    db.query(EssayTask).filter(EssayTask.is_active == True).update({"is_active": False})
    db.commit()
    return {"message": "已取消所有活跃任务"}
