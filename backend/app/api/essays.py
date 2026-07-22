import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta

from ..database import get_db
from ..models.models import User, Essay, Class, UserClass
from ..schemas.schemas import EssayCreate, EssayOut
from ..utils.auth import get_current_user
from ..utils.file_utils import (
    get_essay_dir, generate_essay_filename, generate_correction_filename,
    has_correction, count_corrections_in_dir, get_upload_dir,
)

router = APIRouter(prefix="/api/essays", tags=["作文"])


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
    class_id: int = Form(...),
    grade: str = Form(""),
    essay_number: int = Form(1),
    essay_title: str = Form(""),
    student_name: str = Form(...),
    is_supplement: bool = Form(False),
    teaching_mode: str = Form("线下"),
    remark: str = Form(""),
    content_text: str = Form(""),
    files: list[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 检查权限（暂时放宽：收集者直接通过）
    if "collector" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    # 确定文件类型
    file_type = "text"
    content_file = ""

    # 创建数据库记录（先获取 ID）
    essay = Essay(
        class_id=class_id,
        grade=grade,
        essay_number=essay_number,
        essay_title=essay_title,
        student_name=student_name,
        is_supplement=is_supplement,
        teaching_mode=teaching_mode,
        remark=remark,
        content_text=content_text,
        file_type=file_type,
        collected_by=current_user.id,
        status="pending",
    )
    db.add(essay)
    db.commit()
    db.refresh(essay)

    # 保存文件
    now = datetime.now()
    ts = now.strftime("%H%M%S")
    cls = db.query(Class).filter(Class.id == class_id).first()
    collector_name = current_user.nickname or current_user.username

    dir_path = get_essay_dir(
        str(now.year), f"{now.month}月", str(now.day),
        grade or "未定年级", essay_number, collector_name, student_name, teaching_mode,
    )
    os.makedirs(dir_path, exist_ok=True)

    uploaded_files = []

    if files:
        # 按上传顺序重命名图片
        img_index = 1
        for f in files:
            if not f.filename:
                continue
            ext = os.path.splitext(f.filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                file_type = "image"
                essay.file_type = file_type
                # 图片按顺序重命名: 1.ext, 2.ext ...
                img_name = f"{img_index}{ext}"
                img_index += 1
                img_path = os.path.join(dir_path, img_name)
                content = await f.read()
                with open(img_path, "wb") as fw:
                    fw.write(content)
                uploaded_files.append(img_name)
            elif ext in [".docx", ".doc"]:
                file_type = "docx"
                essay.file_type = file_type
                safe_filename = generate_essay_filename(
                    essay_title, student_name, essay_number,
                    is_supplement, remark, ts, ext,
                )
                file_path = os.path.join(dir_path, safe_filename)
                content = await f.read()
                with open(file_path, "wb") as fw:
                    fw.write(content)
                uploaded_files.append(safe_filename)

        # 主文件路径指向第一个上传的文件
        if uploaded_files:
            essay.content_file = os.path.relpath(os.path.join(dir_path, uploaded_files[0]), get_upload_dir())
    elif content_text.strip():
        # 只有文字内容 → 用模板生成 docx
        from docx import Document
        from docx.shared import Pt

        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "$MMM $DD.docx"
        )

        doc = Document(template_path)

        # 直接编辑模板文档，保留所有格式（包括分页符等）
        # 在"修改前："段落之后（分页符之前）插入作文内容
        from docx.shared import Pt

        insert_after_idx = None
        for i, p in enumerate(doc.paragraphs):
            if p.text.strip() == "修改前：":
                insert_after_idx = i
                break

        if insert_after_idx is not None:
            insert_after = doc.paragraphs[insert_after_idx]
            new_para = doc.add_paragraph()
            run = new_para.add_run(content_text)
            run.font.size = Pt(12)

            # 把新段落移动到 insert_after 后面
            new_p_element = new_para._element
            target_p_element = insert_after._element
            target_p_element.addnext(new_p_element)

        safe_filename = generate_essay_filename(
            essay_title, student_name, essay_number,
            is_supplement, remark, ts, ".docx",
        )
        file_path = os.path.join(dir_path, safe_filename)
        doc.save(file_path)
        essay.content_file = os.path.relpath(file_path, get_upload_dir())
        essay.file_type = "docx"

    db.commit()

    db.refresh(essay)
    return _essay_to_out(essay, db)


@router.get("")
def list_essays(
    class_id: int = None,
    status: str = None,
    name: str = None,
    grade: str = None,
    essay_number: int = None,
    teaching_mode: str = None,
    reviewer: str = None,
    remark: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Essay)

    # 权限过滤
    if "admin" not in current_user.role:
        if "collector" in current_user.role:
            q = q.filter(Essay.collected_by == current_user.id)
        elif "reviewer" in current_user.role:
            q = q.filter(Essay.reviewer_id == current_user.id)
        else:
            q = q.filter(Essay.collected_by == current_user.id)

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
    if reviewer:
        q = q.join(User, User.id == Essay.collected_by).filter(
            User.nickname.like(f"%{reviewer}%") | User.username.like(f"%{reviewer}%")
        )

    # 排序
    allowed_sort = {"created_at": Essay.created_at, "corrected_at": Essay.corrected_at, "student_name": Essay.student_name, "grade": Essay.grade, "essay_number": Essay.essay_number}
    order_col = allowed_sort.get(sort_by, Essay.created_at)
    if sort_order == "asc":
        q = q.order_by(order_col.asc())
    else:
        q = q.order_by(order_col.desc())

    # 分页
    from sqlalchemy import func as sa_func
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)

    essays = q.all()

    # 过滤掉文件不存在的记录
    result = []
    for e in essays:
        if e.content_file:
            from ..utils.file_utils import get_upload_dir
            import os
            full = os.path.join(get_upload_dir(), e.content_file)
            if not os.path.exists(full):
                continue
        result.append(_essay_to_out(e, db))

    total_valid = len(result)
    pending_total = db.query(sa_func.count(Essay.id)).filter(Essay.status == "pending").scalar() or 0
    corrected_total = db.query(sa_func.count(Essay.id)).filter(Essay.status == "corrected").scalar() or 0

    return {
        "items": result,
        "total": total,
        "pending": pending_total,
        "corrected": corrected_total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/pending", response_model=list[EssayOut])
def pending_essays(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取待批改的作文列表（批改者用）"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    essays = db.query(Essay).filter(
        Essay.status == "pending",
    ).order_by(Essay.created_at.asc()).all()

    result = []
    from ..utils.file_utils import get_upload_dir
    import os
    for e in essays:
        if e.content_file:
            full = os.path.join(get_upload_dir(), e.content_file)
            if not os.path.exists(full):
                continue
        result.append(_essay_to_out(e, db))
    return result


@router.get("/stats")
def essay_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard 统计数据"""
    now = datetime.now()
    today = now.date()
    month_start = today.replace(day=1)

    # 基础计数
    total = db.query(func.count(Essay.id)).scalar() or 0
    pending = db.query(func.count(Essay.id)).filter(Essay.status == "pending").scalar() or 0
    corrected = db.query(func.count(Essay.id)).filter(Essay.status == "corrected").scalar() or 0
    this_month = db.query(func.count(Essay.id)).filter(Essay.created_at >= month_start).scalar() or 0

    # 年级分布
    grade_rows = (
        db.query(Essay.grade, func.count(Essay.id))
        .group_by(Essay.grade)
        .order_by(func.count(Essay.id).desc())
        .all()
    )
    grade_dist = [{"name": g or "未知", "value": c} for g, c in grade_rows]

    # 班级分布
    class_rows = (
        db.query(Class.name, func.count(Essay.id))
        .join(Class, Class.id == Essay.class_id)
        .group_by(Essay.class_id)
        .order_by(func.count(Essay.id).desc())
        .all()
    )
    class_dist = [{"name": n, "value": c} for n, c in class_rows]

    # 助教收集排行（collector 角色用户）
    collector_rows = (
        db.query(User.nickname, User.username, func.count(Essay.id))
        .join(User, User.id == Essay.collected_by)
        .filter(User.role.like("%collector%"))
        .group_by(Essay.collected_by)
        .order_by(func.count(Essay.id).desc())
        .limit(10)
        .all()
    )
    collector_rank = [{"name": n or u, "value": c} for n, u, c in collector_rows]

    # 近 14 天每日上传+批改趋势
    trend = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time())
        d_end = datetime.combine(d, datetime.max.time())
        uploaded = db.query(func.count(Essay.id)).filter(
            Essay.created_at >= d_start, Essay.created_at <= d_end
        ).scalar() or 0
        done = db.query(func.count(Essay.id)).filter(
            Essay.corrected_at >= d_start, Essay.corrected_at <= d_end
        ).scalar() or 0
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

    # 收集所有相关目录
    dirs = set()
    for e in essays:
        if e.content_file:
            d = os.path.dirname(os.path.join(get_upload_dir(), e.content_file))
            dirs.add(d)

    # 创建临时打包目录
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    archive_name = f"{cls.name}_作文打包"
    if essay_number:
        archive_name += f"_第{essay_number}次"
    archive_name += ".tar.gz"

    archive_path = os.path.join(tmp_dir, archive_name)

    # 打包
    import tarfile
    with tarfile.open(archive_path, "w:gz") as tar:
        for d in dirs:
            if os.path.exists(d):
                arcname = os.path.basename(os.path.dirname(d))
                tar.add(d, arcname=os.path.relpath(d, get_upload_dir()))

    return FileResponse(archive_path, filename=archive_name, media_type="application/gzip")


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


@router.post("/{essay_id}/claim")
def claim_essay(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批改者认领作文"""
    if "reviewer" not in current_user.role and "admin" not in current_user.role:
        raise HTTPException(status_code=403, detail="无权限")

    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if essay.reviewer_id:
        raise HTTPException(status_code=400, detail="该作文已被其他人认领")

    essay.reviewer_id = current_user.id
    # 保持 pending 状态，不走 correcting
    db.commit()
    return {"message": "认领成功"}


@router.delete("/{essay_id}")
def delete_essay(
    essay_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除作文（含文件，force=true时强制删除已批改文件）"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if "admin" not in current_user.role and essay.collected_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限删除此作文")

    # 检查是否有批改文件
    from ..utils.file_utils import get_upload_dir, has_correction
    if essay.content_file:
        file_path = os.path.join(get_upload_dir(), essay.content_file)
        orig_dir = os.path.dirname(file_path)
        orig_name = os.path.basename(file_path)
        corr_exists = has_correction(orig_dir, orig_name)
        if corr_exists and not force:
            raise HTTPException(status_code=400, detail="作文已有批改结果，请确认强制删除")

    # 删除相关文件
    if essay.content_file:
        import shutil
        dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    db.delete(essay)
    db.commit()
    return {"message": "删除成功"}


@router.put("/{essay_id}", response_model=EssayOut)
def update_essay(
    essay_id: int,
    grade: str = "",
    essay_number: int = None,
    essay_title: str = "",
    student_name: str = "",
    teaching_mode: str = "",
    remark: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新作文信息"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    # 权限：管理员可改所有，收集者只能改自己上传的
    if "admin" not in current_user.role and essay.collected_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限编辑此作文")
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
    db.commit()
    db.refresh(essay)
    return _essay_to_out(essay, db)


@router.post("/{essay_id}/upload-correction")
async def upload_correction(
    essay_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传批改结果"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if essay.reviewer_id and essay.reviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="该作文不是你的任务")
    if not essay.content_file:
        raise HTTPException(status_code=400, detail="原文不存在，无法上传批改")

    original_path = os.path.join(get_upload_dir(), essay.content_file)
    original_dir = os.path.dirname(original_path)
    original_name = os.path.basename(original_path)

    corr_name = generate_correction_filename(original_name)
    corr_path = os.path.join(original_dir, corr_name)

    content = await file.read()
    with open(corr_path, "wb") as f:
        f.write(content)

    essay.reviewer_id = current_user.id
    essay.status = "corrected"
    essay.corrected_at = datetime.now()
    db.commit()

    return {"message": "批改上传成功", "file": corr_name}


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
    """下载原文：图片打包zip，docx直接下载"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay or not essay.content_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    dir_path = os.path.dirname(os.path.join(get_upload_dir(), essay.content_file))
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查目录下的文件类型
    files = os.listdir(dir_path)
    images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and not f.startswith('改_')]
    has_non_image = any(not f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and not f.startswith('改_') and not f.startswith('.') for f in files)

    if images and not has_non_image and len(images) > 1:
        # 纯多图片 → 打包zip下载
        import tempfile, zipfile
        zip_buffer = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img in sorted(images):
                img_path = os.path.join(dir_path, img)
                zf.write(img_path, img)
        zip_buffer.close()
        student_name = essay.student_name if essay.student_name else "作文"
        return FileResponse(zip_buffer.name, filename=f"{student_name}.zip", media_type="application/zip")
    else:
        # 单文件（一张图片或docx）直接返回
        file_path = os.path.join(dir_path, essay.content_file.rsplit('/', 1)[-1] if '/' in essay.content_file else essay.content_file)
        if not os.path.exists(file_path):
            # 取第一个非改文件
            for f in sorted(files):
                if not f.startswith('改_') and not f.startswith('.'):
                    file_path = os.path.join(dir_path, f)
                    break
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        import mimetypes
        media_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        filename = os.path.basename(file_path)
        return FileResponse(file_path, filename=filename)


@router.get("/{essay_id}/download-correction")
def download_correction(
    essay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载批改结果"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay or not essay.content_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    original_path = os.path.join(get_upload_dir(), essay.content_file)
    original_dir = os.path.dirname(original_path)
    original_name = os.path.basename(original_path)

    corr_name = generate_correction_filename(original_name)
    corr_path = os.path.join(original_dir, corr_name)

    if not os.path.exists(corr_path):
        raise HTTPException(status_code=404, detail="批改结果不存在")

    filename = os.path.basename(corr_path)
    return FileResponse(corr_path, filename=filename)


def _essay_to_out(essay: Essay, db: Session) -> EssayOut:
    collector = db.query(User).filter(User.id == essay.collected_by).first()
    reviewer = db.query(User).filter(User.id == essay.reviewer_id).first() if essay.reviewer_id else None
    class_ = db.query(Class).filter(Class.id == essay.class_id).first()

    # 检查是否有批改文件
    corr_exists = False
    file_path = ""
    if essay.content_file:
        file_path = os.path.join(get_upload_dir(), essay.content_file)
        original_dir = os.path.dirname(file_path)
        original_name = os.path.basename(file_path)
        corr_exists = has_correction(original_dir, original_name)

    # 自动同步状态
    if corr_exists and essay.status != "corrected":
        from datetime import datetime
        essay.status = "corrected"
        essay.corrected_at = datetime.now()
        db.commit()

    return EssayOut(
        id=essay.id,
        class_id=essay.class_id,
        class_name=class_.name if class_ else "",
        grade=essay.grade or "",
        essay_number=essay.essay_number or 0,
        essay_title=essay.essay_title or "",
        student_name=essay.student_name,
        is_supplement=essay.is_supplement or False,
        teaching_mode=essay.teaching_mode or "线下",
        remark=essay.remark or "",
        content_text=essay.content_text or "",
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
    )
