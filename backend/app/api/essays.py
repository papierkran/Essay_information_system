import os
import json
import shutil
import tempfile
import zipfile
import uuid
import threading
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models.models import User, Essay, Class, UserClass, EssayTask, OperationLog, SystemConfig, EssayImage
from ..schemas.schemas import EssayCreate, EssayOut, TaskOut, OperationLogOut
from ..utils.auth import get_current_user
from ..utils.file_utils import (
    get_essay_dir, generate_essay_filename, generate_correction_filename,
    has_correction, count_corrections_in_dir, get_upload_dir,
)
from ..utils.ocr_utils import ocr_essay_images, ai_correct_text, ai_rewrite_text, count_cjk_chars

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
    now = datetime.now()
    tasks = db.query(EssayTask).filter(
        EssayTask.is_active == True,
        (EssayTask.deadline == None) | (EssayTask.deadline >= now)
    ).all()
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
    
    total = db.query(func.count(Essay.id)).filter(
        Essay.task_id == task_id,
        Essay.deleted_at == None
    ).scalar() or 0
    pending = db.query(func.count(Essay.id)).filter(
        Essay.task_id == task_id,
        Essay.deleted_at == None,
        Essay.status.in_(["pending", "confirming"])
    ).scalar() or 0
    confirming = db.query(func.count(Essay.id)).filter(
        Essay.task_id == task_id,
        Essay.deleted_at == None,
        Essay.status == "confirming"
    ).scalar() or 0
    corrected = db.query(func.count(Essay.id)).filter(
        Essay.task_id == task_id,
        Essay.deleted_at == None,
        Essay.status == "corrected"
    ).scalar() or 0
    
    return {
        "task_id": task_id,
        "total": total,
        "pending": pending,
        "confirming": confirming,
        "corrected": corrected
    }


def _build_download_filename(essay: Essay) -> str:
    """构建规范的下载文件名：标题——学生姓名年级第N次线上/线下补交（第几次为0或空时省略）"""
    title = essay.essay_title or "无标题"
    student = essay.student_name or "未知"
    grade = essay.grade or ""
    mode = essay.teaching_mode or "线下"
    supp = "补交" if essay.is_supplement else ""
    if essay.essay_number:
        return f"{title}——{student}{grade}第{essay.essay_number}次{mode}{supp}"
    return f"{title}——{student}{grade}{mode}{supp}"


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


@router.get("/collectors")
def list_collectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取收集者列表（用于筛选下拉）"""
    collectors = db.query(User).filter(
        User.deleted_at == None,
        (User.role.like('%collector%') | User.role.like('%admin%'))
    ).all()
    return [{"id": u.id, "nickname": u.nickname or u.username} for u in collectors]


@router.get("/recent-titles")
def list_recent_titles(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取最近上传的作文标题列表"""
    rows = (
        db.query(Essay.essay_title)
        .filter(Essay.deleted_at == None, Essay.essay_title != None, Essay.essay_title != "")
        .order_by(Essay.created_at.desc())
        .limit(limit * 3)
        .all()
    )
    seen = set()
    result = []
    for (title,) in rows:
        if title not in seen:
            seen.add(title)
            result.append(title)
        if len(result) >= limit:
            break
    return result


@router.get("/reviewers")
def list_reviewers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取修改者列表（用于筛选下拉）"""
    reviewers = db.query(User).filter(
        User.deleted_at == None,
        (User.role.like('%reviewer%') | User.role.like('%admin%'))
    ).all()
    return [{"id": u.id, "nickname": u.nickname or u.username} for u in reviewers]


def get_collector_classes(user: User, db: Session) -> list[int]:
    """获取用户负责的班级 ID 列表"""
    ucs = db.query(UserClass).filter(
        UserClass.user_id == user.id,
        UserClass.role_in_class == "collector",
    ).all()
    return [uc.class_id for uc in ucs]


def _log_operation(db: Session, essay_id: int, user_id: int, action: str, detail: str = "",
                   old_value: str = "", new_value: str = "", batch_id: str = "", essay_ids: str = ""):
    try:
        log = OperationLog(
            essay_id=essay_id,
            user_id=user_id,
            action=action,
            detail=detail,
            old_value=old_value,
            new_value=new_value,
            batch_id=batch_id or None,
            essay_ids=essay_ids or None,
        )
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
    collector_note: str = Form(""),
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
        essay.collector_note = collector_note
        if content_text:
            essay.content_text = content_text
        if essay.content_file and files:
            old_dir = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
            if os.path.exists(old_dir) and get_upload_dir() in old_dir:
                shutil.rmtree(old_dir, ignore_errors=True)
            db.query(EssayImage).filter(EssayImage.essay_id == essay.id).delete()
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"学生「{student_name}」的同一篇作文已存在（第{essay_number}次{'补交' if is_supplement else '正篇'}），请先删除重复记录"
            )
        db.refresh(essay)
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
                collector_note=collector_note,
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
        f"{grade_name}第{essay_number}次" if essay_number not in (None, 0) else grade_name,
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
                essay_image = EssayImage(essay_id=essay.id, filename=img_name, image_data=content)
                db.add(essay_image)
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

                # 解析docx内容作为修改前内容
                if not essay.content_text and ext == ".docx":
                    try:
                        from docx import Document
                        import io
                        doc = Document(io.BytesIO(content))
                        text_lines = []
                        for para in doc.paragraphs:
                            if para.text.strip():
                                text_lines.append(para.text.strip())
                        if text_lines:
                            essay.content_text = "\n".join(text_lines)
                    except Exception:
                        pass

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
    is_supplement: bool = Form(False),
    task_id: int = Form(None),
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
        f"{grade_name}第{essay_number}次" if essay_number not in (None, 0) else grade_name,
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
        # 检查是否已存在同一条记录（同一学生同一次作文，优先匹配同一任务）
        existing_query = db.query(Essay).filter(
            Essay.class_id == 1,
            Essay.student_name == student_name,
            Essay.essay_number == essay_number,
            Essay.is_supplement == is_supplement,
            Essay.deleted_at == None,
        )
        if task_id is not None:
            existing_query = existing_query.filter(Essay.task_id == task_id)
        existing = existing_query.first()

        if existing:
            # 更新已有记录
            existing.essay_title = essay_title or existing.essay_title
            existing.content_text = content_text or existing.content_text
            existing.corrected_text = corrected_text if corrected_text else existing.corrected_text
            existing.status = "confirming" if corrected_text and existing.status == "pending" and existing.content_text and existing.content_text.strip() else existing.status
            existing.corrected_at = datetime.now() if corrected_text else existing.corrected_at
            existing.reviewer_id = current_user.id if corrected_text else existing.reviewer_id
            existing.teaching_mode = teaching_mode or existing.teaching_mode
            existing.collected_by = collector_id
            existing.is_supplement = is_supplement
            if task_id is not None:
                existing.task_id = task_id
            essay = existing
        else:
            # 新建记录
            essay = Essay(
                class_id=1,
                grade=grade,
                essay_number=essay_number,
                essay_title=essay_title,
                student_name=student_name,
                is_supplement=is_supplement,
                teaching_mode=teaching_mode,
                remark="",
                content_text=content_text,
                corrected_text=corrected_text if corrected_text else "",
                file_type="docx",
                collected_by=collector_id,
                task_id=task_id,
                status="confirming" if corrected_text and content_text and content_text.strip() else "pending",
                corrected_at=datetime.now() if corrected_text else None,
                reviewer_id=current_user.id if corrected_text else None,
            )
            db.add(essay)

        db.flush()
        _log_operation(db, essay.id, current_user.id, "修改", student_name)
        db.commit()
        db.refresh(essay)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"学生「{student_name}」第{essay_number}次作文在所选任务下已存在，请先删除重复记录"
        )
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
    task_id: int = None,
    reviewer_id: int = None,
    is_supplement: bool = None,
    task_name: str = None,
    word_count_min: int = None,
    word_count_max: int = None,
    corrected_word_count_min: int = None,
    corrected_word_count_max: int = None,
    date_from: str = None,
    date_to: str = None,
    corrected_from: str = None,
    corrected_to: str = None,
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
        q = q.filter(Essay.collector_note.like(f"%{remark}%"))
    if collected_by:
        q = q.filter(Essay.collected_by == collected_by)
    if essay_title:
        q = q.filter(Essay.essay_title.like(f"%{essay_title}%"))
    if task_id is not None:
        q = q.filter(Essay.task_id == task_id)
    if reviewer_id is not None:
        q = q.filter(Essay.reviewer_id == reviewer_id)
    if is_supplement is not None:
        q = q.filter(Essay.is_supplement == is_supplement)
    if task_name:
        q = q.join(EssayTask, Essay.task_id == EssayTask.id, isouter=True).filter(EssayTask.name.like(f"%{task_name}%"))
    if word_count_min is not None:
        q = q.filter(func.char_length(Essay.content_text) >= word_count_min)
    if word_count_max is not None:
        q = q.filter(func.char_length(Essay.content_text) <= word_count_max)
    if corrected_word_count_min is not None:
        q = q.filter(func.char_length(Essay.corrected_text) >= corrected_word_count_min)
    if corrected_word_count_max is not None:
        q = q.filter(func.char_length(Essay.corrected_text) <= corrected_word_count_max)
    if date_from:
        q = q.filter(Essay.created_at >= date_from)
    if date_to:
        q = q.filter(Essay.created_at <= date_to + " 23:59:59")
    if corrected_from:
        q = q.filter(Essay.corrected_at >= corrected_from)
    if corrected_to:
        q = q.filter(Essay.corrected_at <= corrected_to + " 23:59:59")

    # 排序
    from sqlalchemy import case
    allowed_sort = {"created_at": Essay.created_at, "corrected_at": Essay.corrected_at, "student_name": Essay.student_name, "grade": Essay.grade, "essay_number": Essay.essay_number, "status": Essay.status, "remark": Essay.remark, "is_supplement": Essay.is_supplement}
    
    # 处理特殊排序字段
    if sort_by == "collector_name":
        q = q.outerjoin(User, User.id == Essay.collected_by)
        order_col = User.nickname
    elif sort_by == "reviewer_name":
        q = q.outerjoin(User, User.id == Essay.reviewer_id)
        order_col = User.nickname
    elif sort_by == "word_count":
        order_col = func.char_length(Essay.content_text)
    elif sort_by == "corrected_word_count":
        order_col = func.char_length(Essay.corrected_text)
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

    pending_total = db.query(sa_func.count(Essay.id)).filter(Essay.status.in_(["pending", "confirming"]), Essay.file_saved == True).scalar() or 0
    correcting_total = db.query(sa_func.count(Essay.id)).filter(Essay.status == "confirming", Essay.file_saved == True).scalar() or 0
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


@router.get("/pending")
def pending_essays(
    name: str = None,
    grade: str = None,
    essay_number: int = None,
    teaching_mode: str = None,
    task_id: int = None,
    task_name: str = None,
    collected_by: int = None,
    essay_title: str = None,
    status: str = None,
    date_from: str = None,
    date_to: str = None,
    sort_by: str = "created_at",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取待修改的作文列表（修改者/游客用），支持筛选和分页"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role and "guest" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    q = db.query(Essay).filter(
        Essay.deleted_at == None,
        Essay.file_saved == True,
    )

    if status:
        q = q.filter(Essay.status == status)
    else:
        q = q.filter(Essay.status.in_(["pending", "confirming"]))
    if name:
        q = q.filter(Essay.student_name.like(f"%{name}%"))
    if grade:
        q = q.filter(Essay.grade == grade)
    if essay_number:
        q = q.filter(Essay.essay_number == essay_number)
    if teaching_mode:
        q = q.filter(Essay.teaching_mode == teaching_mode)
    if task_id is not None:
        q = q.filter(Essay.task_id == task_id)
    if task_name:
        q = q.join(EssayTask, Essay.task_id == EssayTask.id, isouter=True).filter(EssayTask.name.like(f"%{task_name}%"))
    if collected_by:
        q = q.filter(Essay.collected_by == collected_by)
    if essay_title:
        q = q.filter(Essay.essay_title.like(f"%{essay_title}%"))
    if date_from:
        q = q.filter(Essay.created_at >= date_from)
    if date_to:
        q = q.filter(Essay.created_at <= date_to + " 23:59:59")

    allowed_sort = {
        "created_at": Essay.created_at,
        "student_name": Essay.student_name,
        "grade": Essay.grade,
        "essay_number": Essay.essay_number,
    }
    order_col = allowed_sort.get(sort_by, Essay.created_at)
    if sort_order == "desc":
        q = q.order_by(order_col.desc())
    else:
        q = q.order_by(order_col.asc())

    total = q.count()
    essays = q.offset((page - 1) * page_size).limit(page_size).all()
    result = [_essay_to_out(e, db) for e in essays]
    return {"items": result, "total": total, "page": page, "page_size": page_size}


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
    pending = base.filter(Essay.status.in_(["pending", "confirming"])).count()
    confirming = base.filter(Essay.status == "confirming").count()
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
        "confirming": confirming,
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
    _log_operation(db, essay.id, current_user.id, "修改", essay.student_name)
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
        db.query(EssayImage).filter(EssayImage.essay_id == essay_id).delete()
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
    reviewer_note: str = Form(""),
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

    if reviewer_note.strip():
        essay.reviewer_note = reviewer_note.strip()

    essay.reviewer_id = current_user.id
    if essay.status == "pending" and essay.content_text and essay.content_text.strip():
        essay.status = "confirming"
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
    if not essay:
        return {"images": []}

    images = set()

    if essay.content_file:
        dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    images.add(f)

    db_images = db.query(EssayImage).filter(EssayImage.essay_id == essay_id).all()
    for img in db_images:
        images.add(img.filename)

    sorted_images = sorted(images)
    base_url = "/api/essays/" + str(essay_id) + "/file/"
    return {"images": [base_url + img for img in sorted_images], "dir": ""}


@router.get("/{essay_id}/file/{filename}")
def get_essay_file(
    essay_id: int,
    filename: str,
    db: Session = Depends(get_db),
):
    """获取作文目录下的单个文件（无需 JWT，图片显示用）"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")

    if essay.content_file:
        dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
        file_path = os.path.join(dir_path, filename)
        if os.path.exists(file_path):
            import mimetypes
            media_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            return FileResponse(file_path, media_type=media_type)

    db_img = db.query(EssayImage).filter(
        EssayImage.essay_id == essay_id,
        EssayImage.filename == filename,
    ).first()
    if db_img:
        import mimetypes
        media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        from fastapi.responses import Response
        return Response(content=db_img.image_data, media_type=media_type)

    raise HTTPException(status_code=404, detail="文件不存在")


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

    # 收集图片文件（如果存在）
    img_files = []
    dir_path = ""
    if essay.content_file:
        dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
        if os.path.exists(dir_path):
            all_files = os.listdir(dir_path)
            img_files = [f for f in all_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and not f.startswith('改_')]

    has_text = bool(essay.content_text and essay.content_text.strip())

    # 既有文字又有图片 → docx + 图片打包 zip
    if has_text and img_files:
        tmp_docx = _generate_docx(essay, show_corrected=False)
        zip_buffer = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_docx, f"{dl_name}.docx")
            for img in sorted(img_files):
                zf.write(os.path.join(dir_path, img), img)
        zip_buffer.close()
        os.unlink(tmp_docx)
        return FileResponse(zip_buffer.name, filename=f"{dl_name}.zip", media_type="application/zip")

    # 只有文字 → 从 DB 生成 docx
    if has_text:
        tmp_path = _generate_docx(essay, show_corrected=False)
        return FileResponse(
            tmp_path,
            filename=f"{dl_name}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    # 纯图片 → 打包 zip
    if essay.content_file and img_files:
        zip_buffer = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img in sorted(img_files):
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


@router.post("/{essay_id}/ocr")
def ocr_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """对作文图片进行 OCR 识别，提取文字保存到 content_text"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if essay.file_type != "image":
        raise HTTPException(status_code=400, detail="仅支持图片类型的作文进行 OCR")
    if not essay.content_file:
        raise HTTPException(status_code=400, detail="作文无文件")

    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == "ocr").first()
    ocr_cfg = json.loads(cfg_row.config_value) if cfg_row else {}
    if not ocr_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="OCR 功能未启用，请先在系统设置中配置")

    xfyun_cfg = ocr_cfg.get("xfyun", {})
    if not xfyun_cfg.get("url") or not xfyun_cfg.get("appid") or not xfyun_cfg.get("api_key"):
        raise HTTPException(status_code=400, detail="讯飞 OCR 配置不完整")

    essay_dir = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
    try:
        text = ocr_essay_images(essay_dir, xfyun_cfg)
        essay.content_text = text
        _log_operation(db, essay.id, current_user.id, "OCR", "OCR 识别完成")
        db.commit()
        db.refresh(essay)
        return {"content_text": text, "word_count": len(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")


@router.post("/{essay_id}/ai-correct")
def ai_correct_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """对作文内容进行 AI 错别字修正，保存到 corrected_text"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if not essay.content_text or not essay.content_text.strip():
        raise HTTPException(status_code=400, detail="作文无文字内容，请先进行 OCR 或手动输入")

    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == "llm_typo_fix").first()
    if not cfg_row:
        raise HTTPException(status_code=400, detail="AI 错别字修正配置不存在，请先在系统设置中保存一次")
    try:
        llm_cfg = json.loads(cfg_row.config_value) if cfg_row else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="AI 错别字修正配置损坏，请重新保存系统设置")
    if not llm_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="AI 错别字修正未启用，请在系统设置的「修改前-AI错别字修正」中勾选启用并保存")

    try:
        essay_info = {
            "student_name": essay.student_name,
            "grade": essay.grade,
            "essay_number": essay.essay_number,
            "essay_title": essay.essay_title,
            "teaching_mode": essay.teaching_mode,
            "task_name": essay.task.name if essay.task else None,
        }
        result = ai_correct_text(essay.content_text, llm_cfg, essay_info=essay_info)
        corrected_text = result.get("修改后内容", essay.content_text)
        essay.content_text = corrected_text
        if not essay.essay_title or not essay.essay_title.strip():
            title = result.get("作文标题", "")
            if title and title != "未知":
                essay.essay_title = title.strip()
        _log_operation(db, essay.id, current_user.id, "编辑", "AI 错别字修正")
        db.commit()
        db.refresh(essay)
        return {
            "content_text": corrected_text,
            "essay_title": essay.essay_title,
            "metadata": {
                "title": result.get("作文标题", "未知"),
                "author": result.get("作者", "未知"),
                "word_count": result.get("原文字数", "未知"),
                "grade": result.get("年级", "未知"),
                "mode": result.get("线上或线下", "未知"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 错别字修正失败: {str(e)}")


@router.post("/{essay_id}/ai-rewrite")
def ai_rewrite_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """对作文原文进行 AI 改写，结果保存到 corrected_text"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if not essay.content_text or not essay.content_text.strip():
        raise HTTPException(status_code=400, detail="作文无文字内容")

    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == "llm_editor").first()
    if not cfg_row:
        raise HTTPException(status_code=400, detail="AI 改作文配置不存在，请先在系统设置中保存一次")
    try:
        llm_cfg = json.loads(cfg_row.config_value) if cfg_row else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="AI 改作文配置损坏，请重新保存系统设置")
    if not llm_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="AI 改作文未启用，请在系统设置的「修改后-AI改作文」中勾选启用并保存")

    count_min = llm_cfg.get("count_min")
    count_max = llm_cfg.get("count_max")
    if count_min is not None:
        try: count_min = int(count_min)
        except: count_min = None
    if count_max is not None:
        try: count_max = int(count_max)
        except: count_max = None

    try:
        rewritten = ai_rewrite_text(
            essay.content_text, llm_cfg,
            prompt_template=llm_cfg.get("prompt"),
            count_min=count_min, count_max=count_max,
        )
        essay.corrected_text = rewritten
        if essay.status == "pending" and essay.content_text and essay.content_text.strip():
            essay.status = "confirming"
        essay.corrected_at = datetime.now()
        essay.reviewer_id = current_user.id
        _log_operation(db, essay.id, current_user.id, "批改", "AI 改写")
        db.commit()
        db.refresh(essay)
        return {"corrected_text": rewritten, "char_count": count_cjk_chars(rewritten)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 改写失败: {str(e)}")


@router.post("/{essay_id}/confirm")
def confirm_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认修改：将作文从 待确认 改为 已修改"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if essay.status != "confirming":
        raise HTTPException(status_code=400, detail="当前状态不是待确认，无法确认")
    essay.status = "corrected"
    essay.corrected_at = datetime.now()
    essay.reviewer_id = current_user.id
    _log_operation(db, essay.id, current_user.id, "批改", "确认修改")
    db.commit()
    db.refresh(essay)
    return _essay_to_out(essay, db)


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
    skipped = 0
    if "collected_by" in data and data["collected_by"]:
        for e in essays:
            e.collected_by = data["collected_by"]
            updated += 1
    if "task_id" in data:
        from sqlalchemy.exc import IntegrityError
        new_task_id = data["task_id"] if data["task_id"] else None
        for e in essays:
            savepoint = db.begin_nested()
            e.task_id = new_task_id
            try:
                db.flush()
                savepoint.commit()
                updated += 1
            except IntegrityError:
                savepoint.rollback()
                skipped += 1
    db.commit()
    msg = f"已更新 {updated} 条记录，{skipped} 条略过（重复冲突）" if skipped else f"已更新 {updated} 条记录"
    return {"message": msg, "count": updated, "skipped": skipped}


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


@router.post("/batch-ocr")
def batch_ocr_essays(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量 OCR 识别选中作文的图片"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    if not essays:
        raise HTTPException(status_code=404, detail="未找到选中的作文")

    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == "ocr").first()
    ocr_cfg = json.loads(cfg_row.config_value) if cfg_row else {}
    if not ocr_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="OCR 功能未启用，请先在系统设置中配置")
    xfyun_cfg = ocr_cfg.get("xfyun", {})
    if not xfyun_cfg.get("url") or not xfyun_cfg.get("appid") or not xfyun_cfg.get("api_key"):
        raise HTTPException(status_code=400, detail="讯飞 OCR 配置不完整")

    success = 0
    errors = []
    for e in essays:
        if e.file_type != "image" or not e.content_file:
            errors.append({"id": e.id, "student": e.student_name, "reason": "非图片类型或无文件"})
            continue
        try:
            essay_dir = os.path.dirname(os.path.join(get_upload_dir(), e.content_file))
            text = ocr_essay_images(essay_dir, xfyun_cfg)
            e.content_text = text
            _log_operation(db, e.id, current_user.id, "OCR", "批量 OCR 识别完成")
            success += 1
        except Exception as ex:
            errors.append({"id": e.id, "student": e.student_name, "reason": str(ex)})
    db.commit()
    return {"success": success, "errors": errors, "total": len(essays)}


@router.post("/batch-ai-correct")
def batch_ai_correct_essays(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量 AI 错别字修正选中作文的内容"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    if not essays:
        raise HTTPException(status_code=404, detail="未找到选中的作文")

    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == "llm_typo_fix").first()
    if not cfg_row:
        raise HTTPException(status_code=400, detail="AI 错别字修正配置不存在，请先在系统设置中保存一次")
    try:
        llm_cfg = json.loads(cfg_row.config_value) if cfg_row else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="AI 错别字修正配置损坏，请重新保存系统设置")
    if not llm_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="AI 错别字修正未启用，请在系统设置的「修改前-AI错别字修正」中勾选启用并保存")

    success = 0
    errors = []
    for e in essays:
        if not e.content_text or not e.content_text.strip():
            errors.append({"id": e.id, "student": e.student_name, "reason": "无文字内容"})
            continue
        try:
            result = ai_correct_text(e.content_text, llm_cfg)
            corrected_text = result.get("修改后内容", e.content_text)
            e.content_text = corrected_text
            _log_operation(db, e.id, current_user.id, "编辑", "批量 AI 错别字修正")
            success += 1
        except Exception as ex:
            errors.append({"id": e.id, "student": e.student_name, "reason": str(ex)})
    db.commit()
    return {"success": success, "errors": errors, "total": len(essays)}


@router.post("/batch-ai-rewrite")
def batch_ai_rewrite_essays(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量 AI 改写（一键修改）选中作文，结果保存到 corrected_text"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    if not essays:
        raise HTTPException(status_code=404, detail="未找到选中的作文")

    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == "llm_editor").first()
    if not cfg_row:
        raise HTTPException(status_code=400, detail="AI 改作文配置不存在，请先在系统设置中保存一次")
    try:
        llm_cfg = json.loads(cfg_row.config_value) if cfg_row else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="AI 改作文配置损坏，请重新保存系统设置")
    if not llm_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="AI 改作文未启用，请在系统设置的「修改后-AI改作文」中勾选启用并保存")

    success = 0
    errors = []
    for e in essays:
        if not e.content_text or not e.content_text.strip():
            errors.append({"id": e.id, "student": e.student_name, "reason": "无文字内容"})
            continue
        try:
            rewritten = ai_rewrite_text(e.content_text, llm_cfg, prompt_template=llm_cfg.get("prompt"))
            e.corrected_text = rewritten
            if e.status == "pending" and e.content_text and e.content_text.strip():
                e.status = "confirming"
            e.corrected_at = datetime.now()
            e.reviewer_id = current_user.id
            _log_operation(db, e.id, current_user.id, "批改", "批量 AI 改写")
            success += 1
        except Exception as ex:
            errors.append({"id": e.id, "student": e.student_name, "reason": str(ex)})
    db.commit()
    return {"success": success, "errors": errors, "total": len(essays)}


@router.post("/batch-confirm")
def batch_confirm_essays(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量确认修改：将选中作文从 待确认 改为 已修改"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    if not essays:
        raise HTTPException(status_code=404, detail="未找到选中的作文")
    count = 0
    for e in essays:
        if e.status == "confirming":
            e.status = "corrected"
            e.corrected_at = datetime.now()
            e.reviewer_id = current_user.id
            _log_operation(db, e.id, current_user.id, "批改", "确认修改")
            count += 1
    db.commit()
    return {"success": count, "total": len(essays)}


# ===== 异步批量任务（后台运行，页面离开后继续执行） =====

def _get_ocr_config(db):
    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == "ocr").first()
    if cfg_row:
        try:
            return json.loads(cfg_row.config_value)
        except json.JSONDecodeError:
            return {}
    return {}

def _get_llm_config(db, key):
    cfg_row = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if cfg_row:
        try:
            return json.loads(cfg_row.config_value)
        except json.JSONDecodeError:
            return {}
    return {}


@router.post("/batch-task/ocr/start")
def start_batch_ocr(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """启动异步批量 OCR 任务"""
    if "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="仅管理员可执行")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    ocr_cfg = _get_ocr_config(db)
    if not ocr_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="OCR 功能未启用")

    task_id = str(uuid.uuid4())[:8]
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    from ..services.task_manager import create_task, run_batch_ocr, update_task

    task = create_task(task_id, "ocr", len(essays))
    thread = threading.Thread(target=run_batch_ocr, args=(
        task_id, essay_ids, current_user.id, ocr_cfg,
        get_db, Essay, _log_operation,
    ), daemon=True)
    thread.start()
    return {"task_id": task_id, "total": len(essays)}


@router.post("/batch-task/ai-correct/start")
def start_batch_ai_correct(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """启动异步批量 AI 错别字修正"""
    if "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="仅管理员可执行")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    llm_cfg = _get_llm_config(db, "llm_typo_fix")
    if not llm_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="AI 错别字修正未启用")

    task_id = str(uuid.uuid4())[:8]
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    from ..services.task_manager import create_task, run_batch_ai_correct

    create_task(task_id, "ai_correct", len(essays))
    thread = threading.Thread(target=run_batch_ai_correct, args=(
        task_id, essay_ids, current_user.id, llm_cfg,
        get_db, Essay, _log_operation,
    ), daemon=True)
    thread.start()
    return {"task_id": task_id, "total": len(essays)}


@router.post("/batch-task/ai-rewrite/start")
def start_batch_ai_rewrite(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """启动异步批量 AI 一键修改"""
    if "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="仅管理员可执行")
    essay_ids = data.get("ids", [])
    if not essay_ids:
        raise HTTPException(status_code=400, detail="未选中任何作文")
    llm_cfg = _get_llm_config(db, "llm_editor")
    if not llm_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="AI 改作文未启用")

    task_id = str(uuid.uuid4())[:8]
    essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    from ..services.task_manager import create_task, run_batch_ai_rewrite

    create_task(task_id, "ai_rewrite", len(essays))
    thread = threading.Thread(target=run_batch_ai_rewrite, args=(
        task_id, essay_ids, current_user.id, llm_cfg,
        get_db, Essay, _log_operation,
    ), daemon=True)
    thread.start()
    return {"task_id": task_id, "total": len(essays)}


@router.get("/batch-task/{task_id}")
def get_batch_task_status(task_id: str):
    """查询批量任务进度"""
    from ..services.task_manager import get_task
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return task


@router.post("/operations/{log_id}/undo")
def undo_operation(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """撤回指定的操作记录"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="操作记录不存在")

    action_str = log.action.value if hasattr(log.action, 'value') else str(log.action)
    undone_count = 0
    essay_ids_list = []

    # 解析批量作文ID
    if log.essay_ids:
        try:
            essay_ids_list = json.loads(log.essay_ids)
        except Exception:
            essay_ids_list = []
    elif log.essay_id:
        essay_ids_list = [log.essay_id]

    for eid in essay_ids_list:
        essay = db.query(Essay).filter(Essay.id == eid).first()
        if not essay:
            continue

        if action_str in ("删除", "DELETE"):
            essay.deleted_at = None
            _log_operation(db, eid, current_user.id, "恢复",
                           f"撤回删除操作", batch_id=log.batch_id)
            undone_count += 1

        elif action_str in ("恢复", "RECOVER"):
            essay.deleted_at = datetime.now()
            _log_operation(db, eid, current_user.id, "删除",
                           f"撤回恢复操作", batch_id=log.batch_id)
            undone_count += 1

        elif action_str in ("上传", "UPLOAD"):
            essay.deleted_at = datetime.now()
            _log_operation(db, eid, current_user.id, "删除",
                           f"撤回上传操作", batch_id=log.batch_id)
            undone_count += 1

        elif action_str in ("修改", "UPDATE", "批改", "CORRECT"):
            data = {}
            if log.old_value:
                try:
                    data = json.loads(log.old_value)
                except Exception:
                    data = {"corrected_text": "", "status": "pending"}
            essay.corrected_text = data.get("corrected_text", "")
            essay.corrected_at = None
            essay.reviewer_id = None
            essay.status = "pending"
            _log_operation(db, eid, current_user.id, "编辑",
                           f"撤回修改操作", batch_id=log.batch_id)
            undone_count += 1

        elif action_str in ("编辑", "EDIT"):
            if log.old_value:
                try:
                    data = json.loads(log.old_value)
                    for field, val in data.items():
                        if hasattr(essay, field):
                            setattr(essay, field, val)
                except Exception:
                    pass
            _log_operation(db, eid, current_user.id, "编辑",
                           f"撤回编辑操作", batch_id=log.batch_id)
            undone_count += 1

        elif action_str in ("OCR",):
            essay.content_text = ""
            _log_operation(db, eid, current_user.id, "编辑",
                           f"撤回OCR操作", batch_id=log.batch_id)
            undone_count += 1

    db.commit()
    return {"message": f"已撤回 {undone_count} 条", "undone_count": undone_count}


@router.post("/batch-upload")
async def batch_upload_essays(
    grade: str = Form(...),
    essay_number: int = Form(...),
    teaching_mode: str = Form("线下"),
    data_list: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量上传：在单个请求中上传多个作文，记录为一条操作日志"""
    if "collector" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    import uuid as _uuid
    batch_uuid = _uuid.uuid4().hex[:12]

    try:
        items = json.loads(data_list)
    except Exception:
        raise HTTPException(status_code=400, detail="数据格式错误，需要 JSON 数组")

    cls = db.query(Class).filter(Class.id == 1).first()
    if not cls:
        raise HTTPException(status_code=400, detail="班级不存在（请先创建班级）")

    now = datetime.now()
    grade_name = f"{grade}{teaching_mode}" if teaching_mode else grade

    dir_path = os.path.join(
        get_upload_dir(), str(now.year), f"{now.month}月", str(now.day),
        f"{grade_name}第{essay_number}次" if essay_number else grade_name,
    )
    os.makedirs(dir_path, exist_ok=True)

    if file and file.filename:
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(dir_path, safe_filename)
        content = await file.read()
        with open(file_path, "wb") as fw:
            fw.write(content)

    created_ids = []
    skipped_students = []

    task_id_from_item = None
    if items:
        task_id_from_item = items[0].get("task_id")

    existing_names = set()
    if task_id_from_item:
        existing = db.query(Essay.student_name).filter(
            Essay.task_id == task_id_from_item,
            Essay.grade == grade,
            Essay.essay_number == essay_number,
            Essay.deleted_at == None,
        ).all()
        existing_names = {row[0] for row in existing}

    seen_in_batch = set()
    for item in items:
        student_name = item.get("student_name", "")
        if student_name in existing_names or student_name in seen_in_batch:
            skipped_students.append(student_name)
            continue
        try:
            essay = Essay(
                class_id=1,
                grade=grade,
                essay_number=essay_number,
                essay_title=item.get("essay_title", ""),
                student_name=student_name,
                is_supplement=item.get("is_supplement", False),
                teaching_mode=teaching_mode,
                remark=item.get("remark", ""),
                content_text=item.get("content_text", ""),
                corrected_text=item.get("corrected_text", ""),
                file_type="docx",
                collected_by=current_user.id,
                task_id=task_id_from_item,
                status="pending",
            )
            db.add(essay)
            db.flush()
            created_ids.append(essay.id)
            seen_in_batch.add(student_name)
        except IntegrityError:
            db.rollback()
            skipped_students.append(student_name)
            continue

    db.commit()

    detail_text = f"批量上传 {len(created_ids)} 篇 ({grade}第{essay_number}次)"
    if skipped_students:
        detail_text += f"，跳过 {len(skipped_students)} 个已存在学生：{'、'.join(skipped_students)}"

    # 插入批量操作日志
    try:
        batch_log = OperationLog(
            essay_id=None,
            user_id=current_user.id,
            action="上传",
            detail=detail_text,
            batch_id=batch_uuid,
            essay_ids=json.dumps(created_ids),
        )
        db.add(batch_log)
        db.commit()
    except Exception:
        pass

    return {"message": detail_text, "count": len(created_ids), "ids": created_ids, "batch_id": batch_uuid, "skipped": skipped_students}


# ===== /{essay_id} 通用路由必须放在所有具名路由之后 =====


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
        essay = db.query(Essay).filter(Essay.id == log.essay_id).first() if log.essay_id else None
        result.append(OperationLogOut(
            id=log.id,
            essay_id=log.essay_id,
            user_id=log.user_id,
            user_name=user.nickname or user.username if user else "未知",
            action=log.action.value if hasattr(log.action, 'value') else log.action,
            old_value=log.old_value or "",
            new_value=log.new_value or "",
            detail=log.detail or "",
            batch_id=log.batch_id,
            essay_ids=log.essay_ids,
            student_name=essay.student_name if essay else "",
            essay_title=essay.essay_title if essay else "",
            essay_number=essay.essay_number if essay else 0,
            created_at=log.created_at,
        ))

    return {"items": result, "total": total, "page": page, "page_size": page_size}


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
    collector_note: str = None,
    reviewer_note: str = None,
    collected_by: int = None,
    is_supplement: bool = None,
    task_id: int = None,
    content_text: str = None,
    corrected_text: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新作文信息"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    # 收集者可修改大部分字段，批改者可修改 reviewer_note
    can_edit = "admin" in current_user.role or essay.collected_by == current_user.id
    can_edit_review_note = can_edit or essay.reviewer_id == current_user.id
    if not can_edit and not can_edit_review_note:
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
    if task_id is not None:
        essay.task_id = task_id if task_id > 0 else None
    if content_text is not None:
        essay.content_text = content_text
    if corrected_text is not None and can_edit:
        essay.corrected_text = corrected_text
    if collector_note is not None and can_edit:
        essay.collector_note = collector_note
    if reviewer_note is not None and can_edit_review_note:
        essay.reviewer_note = reviewer_note

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

    # 构建变更记录
    import json
    changes = {}
    if old_grade != essay.grade:
        changes["grade"] = {"old": old_grade, "new": essay.grade}
    if old_number != essay.essay_number:
        changes["essay_number"] = {"old": old_number, "new": essay.essay_number}
    if old_student != essay.student_name:
        changes["student_name"] = {"old": old_student, "new": essay.student_name}
    if old_mode != essay.teaching_mode:
        changes["teaching_mode"] = {"old": old_mode, "new": essay.teaching_mode}
    if essay_title and essay_title != essay.essay_title:
        changes["essay_title"] = {"old": essay.essay_title, "new": essay_title}
    if remark is not None and remark != essay.remark:
        changes["remark"] = {"old": essay.remark, "new": remark}
    if is_supplement is not None and is_supplement != essay.is_supplement:
        changes["is_supplement"] = {"old": essay.is_supplement, "new": is_supplement}

    old_value = json.dumps(changes, ensure_ascii=False) if changes else ""
    _log_operation(db, essay.id, current_user.id, "编辑", essay.student_name, old_value=old_value, new_value=old_value)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")
    db.refresh(essay)
    return _essay_to_out(essay, db)


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
    if corr_exists and essay.status == "pending" and essay.content_text and essay.content_text.strip():
        essay.status = "confirming"
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
        collector_note=essay.collector_note or "",
        reviewer_note=essay.reviewer_note or "",
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
