import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.models import User, Essay, Class, UserClass, EssayTask, OperationLog
from ..schemas.schemas import EssayCreate, EssayOut, TaskOut, OperationLogOut
from ..utils.auth import get_current_user
from ..utils.file_utils import (
    get_essay_dir, generate_essay_filename, generate_correction_filename,
    has_correction, count_corrections_in_dir, get_upload_dir,
)

router = APIRouter(prefix="/api/essays", tags=["作文"])


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有任务列表（供上传选择用）"""
    tasks = db.query(EssayTask).order_by(EssayTask.created_at.desc()).all()
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/tasks/active", response_model=list[TaskOut])
def get_active_tasks(
    db: Session = Depends(get_db),
):
    """获取所有活跃的收集任务（公开接口）"""
    tasks = db.query(EssayTask).filter(EssayTask.is_active == True).all()
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}/stats")
def get_task_stats(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定任务的统计数据"""
    task = db.query(EssayTask).filter(EssayTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    total = db.query(func.count(Essay.id)).filter(Essay.task_id == task_id).scalar() or 0
    pending = db.query(func.count(Essay.id)).filter(
        Essay.task_id == task_id,
        Essay.status == "pending"
    ).scalar() or 0
    corrected = db.query(func.count(Essay.id)).filter(
        Essay.task_id == task_id,
        Essay.status == "corrected"
    ).scalar() or 0
    
    return {
        "task_id": task_id,
        "total": total,
        "pending": pending,
        "corrected": corrected
    }


def _build_download_filename(essay: Essay) -> str:
    """构建规范的下载文件名：标题——学生姓名第N次线上/线下补交"""
    title = essay.essay_title or "无标题"
    student = essay.student_name or "未知"
    n = essay.essay_number or 1
    mode = essay.teaching_mode or "线下"
    supp = "补交" if essay.is_supplement else ""
    return f"{title}——{student}第{n}次{mode}{supp}"


def _generate_docx(essay: Essay, show_corrected: bool = False) -> str:
    """从 DB 生成 docx，返回临时文件路径。show_corrected=True 时包含修改后内容。"""
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_LINE_SPACING
    from docx.oxml.ns import qn

    content = (essay.content_text or "").replace('\r\n', '\n').replace('\r', '\n')
    corrected = (essay.corrected_text or "").replace('\r\n', '\n').replace('\r', '\n')

    doc = Document()

    def _set_run_font(run):
        run.font.name = '宋体'
        run.font.size = Pt(12)
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    def _set_para_format(para, is_title=False):
        fmt = para.paragraph_format
        fmt.line_spacing = Pt(12)
        fmt.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(0)
        if not is_title:
            fmt.first_line_indent = Cm(0.74)
        else:
            fmt.first_line_indent = Cm(0)
            fmt.alignment = 1  # CENTER

    def _add_block(text, label):
        h = doc.add_paragraph()
        h_run = h.add_run(label)
        _set_run_font(h_run)
        _set_para_format(h, is_title=False)

        if not text.strip():
            return
        lines = [l.strip() for l in text.split('\n')]
        non_empty = [l for l in lines if l]
        for idx, line_text in enumerate(non_empty):
            p = doc.add_paragraph()
            run = p.add_run(line_text)
            _set_run_font(run)
            if idx < 2:
                run.bold = True
                _set_para_format(p, is_title=True)
            else:
                _set_para_format(p, is_title=False)

    # 修改前
    _add_block(content, "修改前：")

    if show_corrected:
        # 分页符
        doc.add_page_break()
        # 修改后
        _add_block(corrected, "修改后：")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp_path = tmp.name
    tmp.close()
    doc.save(tmp_path)
    return tmp_path


@router.get("/classes")
def list_classes_public(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """公开班级列表（收集者选班级用）"""
    classes = db.query(Class).all()
    return [{"id": c.id, "name": c.name, "org_id": c.org_id} for c in classes]


def get_collector_classes(user: User, db: Session) -> list[int]:
    """获取用户负责的班级 ID 列表"""
    ucs = db.query(UserClass).filter(
        UserClass.user_id == user.id,
        UserClass.role_in_class == "collector",
    ).all()
    return [uc.class_id for uc in ucs]


def _log_operation(db: Session, essay_id: int, user_id: int, action: str, detail: str = ""):
    try:
        log = OperationLog(essay_id=essay_id, user_id=user_id, action=action, detail=detail)
        db.add(log)
    except Exception:
        pass


def build_file_path(db: Session, essay_data: dict) -> tuple[str, str, str, str]:
    """构建文件路径，返回 (dir_path, filename, year, month)"""
    now = datetime.now()
    year = str(now.year)
    month = f"{now.month}月"
    day = f"{now.day}"
    grade = essay_data.get("grade", "") or "未定年级"
    student_name = essay_data.get("student_name", "未知")

    dir_path = get_essay_dir(year, month, day, grade,
                              essay_data["essay_number"], student_name)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path, year, month


@router.post("/upload", response_model=EssayOut)
async def upload_essay(
    essay_id: int = Form(None),
    class_id: int = Form(...),
    task_id: int = Form(None),
    grade: str = Form(""),
    essay_number: int = Form(1),
    essay_title: str = Form(""),
    student_name: str = Form(...),
    is_supplement: bool = Form(False),
    teaching_mode: str = Form("线下"),
    remark: str = Form(""),
    content_text: str = Form(""),
    collected_by: int = Form(None),
    files: list[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 检查权限（暂时放宽：收集者直接通过）
    if "collector" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    # 确定收集者：管理员可指定，否则用当前用户
    collector_id = current_user.id
    if collected_by and "admin" in current_user.role:
        collector_id = collected_by

    # 确定文件类型
    file_type = "text"
    content_file = ""

    # 创建或更新数据库记录
    if essay_id:
        essay = db.query(Essay).filter(Essay.id == essay_id).first()
        if not essay:
            raise HTTPException(status_code=404, detail="作文不存在")
        if "admin" not in current_user.role and essay.collected_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限编辑此作文")
        essay.class_id = class_id
        essay.task_id = task_id
        essay.grade = grade
        essay.essay_number = essay_number
        essay.essay_title = essay_title
        essay.student_name = student_name
        essay.is_supplement = is_supplement
        essay.teaching_mode = teaching_mode
        essay.remark = remark
        essay.content_text = content_text
    else:
        try:
            essay = Essay(
                class_id=class_id,
                task_id=task_id,
                grade=grade,
                essay_number=essay_number,
                essay_title=essay_title,
                student_name=student_name,
                is_supplement=is_supplement,
                teaching_mode=teaching_mode,
                remark=remark,
                content_text=content_text,
                file_type=file_type,
                collected_by=collector_id,
                status="pending",
            )
            db.add(essay)
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"学生「{student_name}」的同一篇作文已存在（第{essay_number}次{'补交' if is_supplement else '正篇'}），如需修改请先删除旧记录"
            )
    _log_operation(db, essay.id, current_user.id, "上传", student_name)
    db.commit()
    db.refresh(essay)

    # 保存文件
    now = datetime.now()
    ts = now.strftime("%H%M%S")

    grade_name = grade if grade else "未定年级"
    if teaching_mode:
        grade_name = f"{grade_name}{teaching_mode}"

    dir_path = os.path.join(
        get_upload_dir(),
        str(now.year),
        f"{now.month}月",
        str(now.day),
        f"{grade_name}第{essay_number}次",
        student_name,
    )
    os.makedirs(dir_path, exist_ok=True)

    if files:
        img_index = 1
        uploaded_files = []
        for f in files:
            if not f.filename:
                continue
            ext = os.path.splitext(f.filename)[1].lower()
            content = await f.read()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                essay.file_type = "image"
                img_name = f"{img_index}{ext}"
                img_index += 1
                img_path = os.path.join(dir_path, img_name)
                with open(img_path, "wb") as fw:
                    fw.write(content)
                uploaded_files.append(img_name)
            elif ext in [".docx", ".doc"]:
                essay.file_type = "docx"
                safe_filename = generate_essay_filename(
                    essay_title, student_name, essay_number,
                    is_supplement, remark, ts, ext,
                )
                file_path = os.path.join(dir_path, safe_filename)
                with open(file_path, "wb") as fw:
                    fw.write(content)
                uploaded_files.append(safe_filename)

        if uploaded_files:
            essay.content_file = os.path.relpath(
                os.path.join(dir_path, uploaded_files[0]), get_upload_dir()
            )

    db.commit()
    db.refresh(essay)
    return _essay_to_out(essay, db)


@router.post("/upload-correction-docx")
async def upload_correction_docx(
    grade: str = Form(...),
    essay_number: int = Form(...),
    teaching_mode: str = Form("线下"),
    student_name: str = Form(...),
    essay_title: str = Form(""),
    content_text: str = Form(""),
    corrected_text: str = Form(""),
    collected_by: int = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量上传修改后docx：保存文件到年级目录，创建作文记录"""
    if "collector" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    # 确定收集者：管理员可指定，否则用当前用户
    collector_id = current_user.id
    if collected_by and "admin" in current_user.role:
        collector_id = collected_by

    cls = db.query(Class).filter(Class.id == 1).first()
    if not cls:
        raise HTTPException(status_code=400, detail="班级不存在（请先创建班级）")

    now = datetime.now()
    grade_name = grade if grade else "未定年级"
    if teaching_mode:
        grade_name = f"{grade_name}{teaching_mode}"

    dir_path = os.path.join(
        get_upload_dir(),
        str(now.year),
        f"{now.month}月",
        str(now.day),
        f"{grade_name}第{essay_number}次",
    )

    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建目录失败: {str(e)}")

    file_saved = False
    if file and file.filename:
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(dir_path, safe_filename)
        try:
            content = await file.read()
            with open(file_path, "wb") as fw:
                fw.write(content)
            file_saved = True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")

    try:
        essay = Essay(
            class_id=1,
            grade=grade,
            essay_number=essay_number,
            essay_title=essay_title,
            student_name=student_name,
            is_supplement=False,
            teaching_mode=teaching_mode,
            remark="",
            content_text=content_text,
            corrected_text=corrected_text if corrected_text else "",
            file_type="docx",
            collected_by=collector_id,
            status="corrected" if corrected_text else "pending",
            corrected_at=datetime.now() if corrected_text else None,
            reviewer_id=current_user.id if corrected_text else None,
        )
        db.add(essay)
        _log_operation(db, essay.id, current_user.id, "修改", student_name)
        db.commit()
        db.refresh(essay)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建记录失败: {str(e)}")

    return {"message": "上传成功", "id": essay.id}


@router.get("")
def list_essays(
    class_id: int = None,
    status: str = None,
    name: str = None,
    grade: str = None,
    essay_number: int = None,
    teaching_mode: str = None,
    collected_by: int = None,
    remark: str = None,
    essay_title: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Essay).filter(Essay.deleted_at == None)

    # 权限过滤：收集者和游客可以查看所有作文，批改者只能看自己的
    if "admin" not in current_user.role and "guest" not in current_user.role:
        if "reviewer" in current_user.role and "collector" not in current_user.role:
            q = q.filter(Essay.reviewer_id == current_user.id)
        # 收集者可以查看所有作文，不做过滤

    if class_id:
        q = q.filter(Essay.class_id == class_id)
    if status:
        q = q.filter(Essay.status == status)
    if name:
        q = q.filter(Essay.student_name.like(f"%{name}%"))
    if grade:
        q = q.filter(Essay.grade == grade)
    if essay_number:
        q = q.filter(Essay.essay_number == essay_number)
    if teaching_mode:
        q = q.filter(Essay.teaching_mode == teaching_mode)
    if remark:
        q = q.filter(Essay.remark.like(f"%{remark}%"))
    if collected_by:
        q = q.filter(Essay.collected_by == collected_by)
    if essay_title:
        q = q.filter(Essay.essay_title.like(f"%{essay_title}%"))

    # 排序
    from sqlalchemy import case
    allowed_sort = {"created_at": Essay.created_at, "corrected_at": Essay.corrected_at, "student_name": Essay.student_name, "grade": Essay.grade, "essay_number": Essay.essay_number, "status": Essay.status, "remark": Essay.remark}
    
    # 处理collector_name排序
    if sort_by == "collector_name":
        q = q.outerjoin(User, User.id == Essay.collected_by)
        order_col = User.nickname
    elif sort_by == "reviewer_name":
        q = q.outerjoin(User, User.id == Essay.reviewer_id)
        order_col = User.nickname
    else:
        order_col = allowed_sort.get(sort_by, Essay.created_at)
    
    if sort_order == "asc":
        q = q.order_by(order_col.asc())
    else:
        q = q.order_by(order_col.desc())

    # 只显示文件已保存的记录
    q = q.filter(Essay.file_saved == True)

    from sqlalchemy import func as sa_func
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    essays = q.all()
    result = [_essay_to_out(e, db) for e in essays]

    pending_total = db.query(sa_func.count(Essay.id)).filter(Essay.status == "pending", Essay.file_saved == True).scalar() or 0
    corrected_total = db.query(sa_func.count(Essay.id)).filter(Essay.status == "corrected", Essay.file_saved == True).scalar() or 0

    # 收集者列表（用于前端下拉筛选）
    collectors = db.query(User).filter(
        User.deleted_at == None,
        (User.role.like('%collector%') | User.role.like('%admin%'))
    ).all()
    collector_list = [{"id": u.id, "nickname": u.nickname or u.username} for u in collectors]

    return {
        "items": result,
        "total": total,
        "pending": pending_total,
        "corrected": corrected_total,
        "collectors": collector_list,
        "page": page,
        "page_size": page_size,
    }


@router.get("/pending", response_model=list[EssayOut])
def pending_essays(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取待修改的作文列表（修改者/游客用）"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role and "guest" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    essays = db.query(Essay).filter(
        Essay.deleted_at == None,
        Essay.status == "pending",
        Essay.file_saved == True,
    ).order_by(Essay.created_at.asc()).all()

    result = [_essay_to_out(e, db) for e in essays]
    return result


@router.get("/trash")
def list_trash(
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查看已删除的作文（管理员）"""
    if "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")
    q = db.query(Essay).filter(Essay.deleted_at != None).order_by(Essay.deleted_at.desc())
    total = q.count()
    essays = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_essay_to_out(e, db) for e in essays],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{essay_id}/restore")
def restore_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从回收站恢复作文"""
    if "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")
    essay = db.query(Essay).filter(Essay.id == essay_id, Essay.deleted_at != None).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在或不在回收站")
    essay.deleted_at = None
    _log_operation(db, essay.id, current_user.id, "恢复", essay.student_name)
    db.commit()
    return {"message": "已恢复"}


@router.get("/stats")
def essay_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard 统计数据"""
    now = datetime.now()
    today = now.date()
    month_start = today.replace(day=1)

    base = db.query(Essay).filter(Essay.deleted_at == None)
    total = base.count()
    pending = base.filter(Essay.status == "pending").count()
    corrected = base.filter(Essay.status == "corrected").count()
    this_month = base.filter(Essay.created_at >= month_start).count()

    grade_rows = (
        base.with_entities(Essay.grade, func.count(Essay.id))
        .group_by(Essay.grade)
        .order_by(func.count(Essay.id).desc())
        .all()
    )
    grade_dist = [{"name": g or "未知", "value": c} for g, c in grade_rows]

    class_rows = (
        base.with_entities(Class.name, func.count(Essay.id))
        .join(Class, Class.id == Essay.class_id)
        .group_by(Class.id, Class.name)
        .order_by(func.count(Essay.id).desc())
        .all()
    )
    class_dist = [{"name": n, "value": c} for n, c in class_rows]

    collector_rows = (
        base.with_entities(User.nickname, User.username, func.count(Essay.id))
        .join(User, User.id == Essay.collected_by)
        .filter(User.role.like("%collector%"))
        .group_by(Essay.collected_by, User.nickname, User.username)
        .order_by(func.count(Essay.id).desc())
        .limit(10)
        .all()
    )
    collector_rank = [{"name": n or u, "value": c} for n, u, c in collector_rows]

    trend = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time())
        d_end = datetime.combine(d, datetime.max.time())
        uploaded = base.filter(Essay.created_at >= d_start, Essay.created_at <= d_end).count()
        done = base.filter(Essay.corrected_at >= d_start, Essay.corrected_at <= d_end).count()
        trend.append({"date": d.strftime("%m-%d"), "uploaded": uploaded, "corrected": done})

    return {
        "total": total,
        "pending": pending,
        "corrected": corrected,
        "this_month": this_month,
        "grade_dist": grade_dist,
        "class_dist": class_dist,
        "collector_rank": collector_rank,
        "trend": trend,
    }


@router.get("/download/by-class/{class_id}")
def download_by_class(
    class_id: int,
    essay_number: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按班级打包下载全部作文"""
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    q = db.query(Essay).filter(Essay.class_id == class_id)
    if essay_number:
        q = q.filter(Essay.essay_number == essay_number)

    essays = q.all()
    if not essays:
        raise HTTPException(status_code=404, detail="没有找到作文")

    dirs = set()
    for e in essays:
        if e.content_file:
            d = os.path.dirname(os.path.join(get_upload_dir(), e.content_file))
            dirs.add(d)

    tmp_dir = tempfile.mkdtemp()
    archive_name = f"{cls.name}_作文打包"
    if essay_number:
        archive_name += f"_第{essay_number}次"
    archive_name += ".tar.gz"

    archive_path = os.path.join(tmp_dir, archive_name)

    import tarfile
    with tarfile.open(archive_path, "w:gz") as tar:
        for d in dirs:
            if os.path.exists(d):
                tar.add(d, arcname=os.path.relpath(d, get_upload_dir()))

    return FileResponse(archive_path, filename=archive_name, media_type="application/gzip")


# ===== 以下所有 /{essay_id}/xxx 具名路由必须在 /{essay_id} 通用路由之前 =====


@router.post("/{essay_id}/claim")
def claim_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改者认领作文"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if essay.reviewer_id:
        raise HTTPException(status_code=400, detail="该作文已被其他人认领")

    essay.reviewer_id = current_user.id
    _log_operation(db, essay.id, current_user.id, "认领", essay.student_name)
    db.commit()
    return {"message": "认领成功"}


@router.delete("/{essay_id}")
def delete_essay(
    essay_id: int,
    delete_file: bool = False,
    permanent: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除作文。
    - 默认：软删除（写入 deleted_at），文件保留
    - delete_file=true：同时删除本地文件（需管理员）
    - permanent=true：物理删除数据库记录（需管理员）
    """
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if "admin" not in current_user.role and essay.collected_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限删除此作文")

    if delete_file:
        if "admin" not in current_user.role:
            raise HTTPException(status_code=403, detail="仅管理员可删除本地文件")
        if essay.content_file:
            dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        essay.content_file = ""

    if permanent:
        if "admin" not in current_user.role:
            raise HTTPException(status_code=403, detail="仅管理员可彻底删除")
        if essay.content_file:
            dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
            if os.path.exists(dir_path) and not delete_file:
                # 如果还没删文件，现在删
                pass  # delete_file 已经处理了
        db.delete(essay)
        _log_operation(db, essay_id, current_user.id, "删除", essay.student_name)
        db.commit()
        return {"message": "已彻底删除"}

    essay.deleted_at = datetime.now()
    _log_operation(db, essay_id, current_user.id, "删除", essay.student_name)
    db.commit()
    return {"message": "已移入回收站"}


@router.post("/{essay_id}/upload-correction")
async def upload_correction(
    essay_id: int,
    file: UploadFile = File(None),
    corrected_text: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传修改结果（支持文件上传 + 文字修改）"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if essay.reviewer_id and essay.reviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="该作文不是你的任务")

    # 至少提供文件或文字
    if not file and not corrected_text.strip():
        raise HTTPException(status_code=400, detail="请上传文件或填写修改文字")

    # 保存文件（如果有）
    corr_name = ""
    if file and file.filename:
        if not essay.content_file:
            raise HTTPException(status_code=400, detail="原文不存在，无法上传修改")
        original_path = os.path.join(get_upload_dir(), essay.content_file)
        original_dir = os.path.dirname(original_path)
        original_name = os.path.basename(original_path)

        corr_name = generate_correction_filename(original_name)
        corr_path = os.path.join(original_dir, corr_name)

        content = await file.read()
        with open(corr_path, "wb") as f:
            f.write(content)

    # 保存文字修改（如果有）
    if corrected_text.strip():
        essay.corrected_text = corrected_text.strip()

    essay.reviewer_id = current_user.id
    essay.status = "corrected"
    essay.corrected_at = datetime.now()
    _log_operation(db, essay.id, current_user.id, "修改", essay.student_name)
    db.commit()

    return {"message": "修改上传成功", "file": corr_name, "corrected_text": essay.corrected_text}


@router.get("/{essay_id}/images")
def get_essay_images(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取作文目录下的所有图片（返回URL列表）"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay or not essay.content_file:
        return {"images": []}

    dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
    if not os.path.exists(dir_path):
        return {"images": []}

    images = sorted([
        f for f in os.listdir(dir_path)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
    ])

    base_url = "/api/essays/" + str(essay_id) + "/file/"
    return {"images": [base_url + img for img in images], "dir": dir_path}


@router.get("/{essay_id}/file/{filename}")
def get_essay_file(
    essay_id: int,
    filename: str,
    db: Session = Depends(get_db),
):
    """获取作文目录下的单个文件（无需 JWT，图片显示用）"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay or not essay.content_file:
        raise HTTPException(status_code=404, detail="作文不存在")

    dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
    file_path = os.path.join(dir_path, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    import mimetypes
    media_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    return FileResponse(file_path, media_type=media_type)


@router.get("/{essay_id}/download")
def download_essay_file(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载原文：有文字内容时从 DB 生成 docx，纯图片时打包 zip"""
    if "guest" in current_user.role:
        raise HTTPException(status_code=403, detail="游客无下载权限")
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")

    dl_name = _build_download_filename(essay)

    # 有文字内容 → 从 DB 生成 docx
    if essay.content_text and essay.content_text.strip():
        tmp_path = _generate_docx(essay, show_corrected=False)
        return FileResponse(
            tmp_path,
            filename=f"{dl_name}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    # 纯图片 → 打包 zip
    if essay.content_file:
        dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and not f.startswith('改_')]
            if images:
                zip_buffer = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for img in sorted(images):
                        zf.write(os.path.join(dir_path, img), img)
                zip_buffer.close()
                return FileResponse(zip_buffer.name, filename=f"{dl_name}.zip", media_type="application/zip")

    # 兜底：返回原始文件
    if essay.content_file:
        file_path = os.path.join(get_upload_dir(), essay.content_file)
        if os.path.exists(file_path):
            import mimetypes
            ext = os.path.splitext(file_path)[1]
            media_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            return FileResponse(file_path, filename=f"{dl_name}{ext}", media_type=media_type)

    raise HTTPException(status_code=404, detail="文件不存在")


@router.get("/{essay_id}/download-correction")
def download_correction(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载修改结果"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay or not essay.content_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    original_path = os.path.join(get_upload_dir(), essay.content_file)
    original_dir = os.path.dirname(original_path)
    original_name = os.path.basename(original_path)

    corr_name = generate_correction_filename(original_name)
    corr_path = os.path.join(original_dir, corr_name)

    if not os.path.exists(corr_path):
        raise HTTPException(status_code=404, detail="修改结果不存在")

    dl_name = _build_download_filename(essay)
    ext = os.path.splitext(corr_path)[1]
    return FileResponse(corr_path, filename=f"{dl_name}{ext}")


@router.get("/{essay_id}/export-docx")
def export_docx(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出修改前后 docx：从 DB 读取 content_text + corrected_text"""
    if "guest" in current_user.role:
        raise HTTPException(status_code=403, detail="游客无导出权限")
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")

    tmp_path = _generate_docx(essay, show_corrected=True)
    dl_name = _build_download_filename(essay)

    return FileResponse(
        tmp_path,
        filename=f"改_{dl_name}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/batch-update")
def batch_update_essays(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量修改选中作文的收集者或任务"""
    if "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="仅管理员可批量修改")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids)).all()
    updated = 0
    if "collected_by" in data and data["collected_by"]:
        for e in essays:
            e.collected_by = data["collected_by"]
            updated += 1
    if "task_id" in data:
        for e in essays:
            e.task_id = data["task_id"]
            updated += 1
    db.commit()
    return {"message": f"已更新 {updated} 条记录", "count": len(essays)}


@router.post("/batch-export-docx")
def batch_export_docx(
    essay_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导出选中作文的docx（修改前后），打包为zip下载"""
    from pydantic import BaseModel

    essays = db.query(Essay).filter(Essay.id.in_(essay_ids)).all()
    if not essays:
        raise HTTPException(status_code=404, detail="未找到选中的作文")

    # 创建临时zip文件
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp_zip_path = tmp_zip.name
    tmp_zip.close()

    try:
        with zipfile.ZipFile(tmp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for essay in essays:
                tmp_docx = _generate_docx(essay, show_corrected=True)
                dl_name = _build_download_filename(essay)
                # 将docx文件添加到zip中
                zf.write(tmp_docx, f"改_{dl_name}.docx")
                # 删除临时docx文件
                os.unlink(tmp_docx)

        # 构建下载文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"作文导出_{timestamp}.zip"

        return FileResponse(
            tmp_zip_path,
            filename=zip_filename,
            media_type="application/zip",
        )
    except Exception as e:
        # 清理临时文件
        if os.path.exists(tmp_zip_path):
            os.unlink(tmp_zip_path)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ===== /{essay_id} 通用路由必须放在所有具名路由之后 =====


@router.get("/{essay_id}", response_model=EssayOut)
def get_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    return _essay_to_out(essay, db)


@router.put("/{essay_id}", response_model=EssayOut)
def update_essay(
    essay_id: int,
    grade: str = "",
    essay_number: int = None,
    essay_title: str = "",
    student_name: str = "",
    teaching_mode: str = "",
    remark: str = "",
    collected_by: int = None,
    is_supplement: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新作文信息"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if "admin" not in current_user.role and essay.collected_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限编辑此作文")

    # 记录修改前的路径关键字段
    old_grade = essay.grade
    old_number = essay.essay_number
    old_student = essay.student_name
    old_mode = essay.teaching_mode

    if grade:
        essay.grade = grade
    if essay_number is not None:
        essay.essay_number = essay_number
    if essay_title:
        essay.essay_title = essay_title
    if student_name:
        essay.student_name = student_name
    if teaching_mode:
        essay.teaching_mode = teaching_mode
    if remark is not None:
        essay.remark = remark
    if collected_by is not None and "admin" in current_user.role:
        essay.collected_by = collected_by
    if is_supplement is not None:
        essay.is_supplement = is_supplement

    # 如果年级/次数/学生/方式变了，移动文件
    new_grade = essay.grade
    new_number = essay.essay_number
    new_student = essay.student_name
    new_mode = essay.teaching_mode

    if (essay.content_file and (
        new_grade != old_grade or
        new_number != old_number or
        new_student != old_student or
        new_mode != old_mode
    )):
        old_dir = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))

        # 构建新目录路径
        from ..utils.file_utils import get_essay_dir, move_content_file
        now = datetime.now()
        task_name = ""
        task_created_at = None
        if essay.task_id:
            task = db.query(EssayTask).filter(EssayTask.id == essay.task_id).first()
            if task:
                task_name = task.name
                task_created_at = task.created_at

        new_dir = get_essay_dir(
            str(now.year), f"{now.month}月", str(now.day),
            new_grade or "未定年级", new_number, "", new_student, new_mode,
            task_name=task_name, task_created_at=task_created_at,
        )

        new_content_file = move_content_file(essay, old_dir, new_dir)
        if new_content_file:
            essay.content_file = new_content_file

    _log_operation(db, essay.id, current_user.id, "编辑", essay.student_name)
    db.commit()
    db.refresh(essay)
    return _essay_to_out(essay, db)


@router.get("/operations")
def list_operations(
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取操作历史列表"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role and "guest" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    q = db.query(OperationLog).order_by(OperationLog.created_at.desc())
    total = q.count()
    logs = q.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        essay = db.query(Essay).filter(Essay.id == log.essay_id).first()
        result.append(OperationLogOut(
            id=log.id,
            essay_id=log.essay_id,
            user_id=log.user_id,
            user_name=user.nickname or user.username if user else "未知",
            action=log.action,
            detail=log.detail or "",
            student_name=essay.student_name if essay else "",
            essay_title=essay.essay_title if essay else "",
            essay_number=essay.essay_number if essay else 0,
            created_at=log.created_at,
        ))

    return {"items": result, "total": total, "page": page, "page_size": page_size}


def _essay_to_out(essay: Essay, db: Session) -> EssayOut:
    collector = db.query(User).filter(User.id == essay.collected_by).first()
    reviewer = db.query(User).filter(User.id == essay.reviewer_id).first() if essay.reviewer_id else None
    class_ = db.query(Class).filter(Class.id == essay.class_id).first()
    task = db.query(EssayTask).filter(EssayTask.id == essay.task_id).first() if essay.task_id else None

    corr_exists = False
    file_path = ""
    if essay.content_file:
        file_path = os.path.join(get_upload_dir(), essay.content_file)
        original_dir = os.path.dirname(file_path)
        original_name = os.path.basename(file_path)
        corr_exists = has_correction(original_dir, original_name)

    # 自动同步状态
    if corr_exists and essay.status != "corrected":
        essay.status = "corrected"
        essay.corrected_at = datetime.now()
        db.commit()

    return EssayOut(
        id=essay.id,
        class_id=essay.class_id,
        class_name=class_.name if class_ else "",
        task_id=essay.task_id,
        task_name=task.name if task else "",
        grade=essay.grade or "",
        essay_number=essay.essay_number or 0,
        essay_title=essay.essay_title or "",
        student_name=essay.student_name,
        is_supplement=essay.is_supplement or False,
        teaching_mode=essay.teaching_mode or "线下",
        remark=essay.remark or "",
        content_text=essay.content_text or "",
        corrected_text=essay.corrected_text or "",
        content_file=essay.content_file or "",
        file_type=essay.file_type or "text",
        collected_by=essay.collected_by,
        collector_name=collector.nickname or collector.username if collector else "未知",
        status=essay.status or "pending",
        reviewer_id=essay.reviewer_id,
        reviewer_name=reviewer.nickname or reviewer.username if reviewer else "",
        corrected_at=essay.corrected_at,
        created_at=essay.created_at,
        file_path=file_path,
        has_correction=corr_exists,
        file_saved=essay.file_saved if essay.file_saved is not None else True,
        word_count=len((essay.content_text or "").replace('\r\n', '\n').replace('\r', '\n').replace(' ', '')),
        corrected_word_count=len((essay.corrected_text or "").replace('\r\n', '\n').replace('\r', '\n').replace(' ', '')),
    )
