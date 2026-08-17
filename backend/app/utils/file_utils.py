import os
import shutil
import json
from datetime import datetime

_SETTINGS = None


def _load_settings():
    global _SETTINGS
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, encoding="utf-8") as f:
            _SETTINGS = json.load(f)
    else:
        _SETTINGS = {"upload_dir": "uploads"}
    return _SETTINGS


def get_upload_dir():
    s = _load_settings()
    return s.get("upload_dir", "uploads")


BASE_UPLOAD_DIR = get_upload_dir()


def safe_component(name: str, fallback: str = "") -> str:
    """清洗路径组件，防止路径穿越（../、/、\\）及控制字符。"""
    if not name:
        return fallback
    cleaned = str(name).replace("\\", "_").replace("/", "_").replace("..", "_").strip().lstrip(".")
    if not cleaned:
        return fallback
    return cleaned


def get_essay_dir(
    year: str,
    month: str,
    day: str,
    grade: str,
    essay_number: int,
    collector_name: str,
    student_name: str = "",
    teaching_mode: str = "",
    task_name: str = "",
    task_created_at: datetime = None,
    essay_title: str = "",
    is_supplement: bool = False,
) -> str:
    """生成作文存储目录路径。
    - 有任务：{年}/{MMDD}_{课程名}/{年级}{方式}第{N}次/{学生}/{标题}/
    - 无任务：{年}/{月}月/{日}/{年级}{方式}第{N}次/{学生}/{标题}/
    """
    grade = safe_component(grade, "未定年级")
    if teaching_mode:
        grade_name = f"{grade}{safe_component(teaching_mode, '')}"
    else:
        grade_name = grade
    task_dir = grade_name if essay_number in (None, 0) else f"{grade_name}第{essay_number}次"

    if task_name and task_created_at:
        task_year = str(task_created_at.year)
        mmdd = task_created_at.strftime("%m%d")
        course = safe_component(task_name, "任务")
        path = os.path.join(
            get_upload_dir(),
            task_year,
            f"{mmdd}_{course}",
            task_dir,
        )
    else:
        path = os.path.join(
            get_upload_dir(),
            safe_component(year, "0000"),
            safe_component(month, "1月"),
            safe_component(day, "1"),
            task_dir,
        )
    if student_name:
        path = os.path.join(path, safe_component(student_name, "未知"))
    if essay_title:
        title_component = safe_component(essay_title, "无标题")
        if is_supplement:
            title_component += "_补交"
        path = os.path.join(path, title_component)
    return path


def generate_essay_filename(
    essay_title: str,
    student_name: str,
    essay_number: int,
    is_supplement: bool,
    remark: str,
    timestamp: str,
    ext: str = ".docx",
) -> str:
    """生成作文文件名"""
    suppl = "补交" if is_supplement else ""
    rm = f"_{safe_component(remark, '')}" if remark else ""
    safe_title = safe_component(essay_title, "无标题") if essay_title else "无标题"
    safe_student = safe_component(student_name, "未知")
    num_part = "" if essay_number in (None, 0) else f"_第{essay_number}次"
    return f"{safe_title}_{safe_student}{num_part}_{suppl}{rm}_{timestamp}{ext}"


def generate_correction_filename(original_filename: str) -> str:
    """生成修改文件名（加 改_ 前缀）"""
    return f"改_{original_filename}"


def has_correction(file_dir: str, original_filename: str) -> bool:
    """判断目录下是否有修改文件（有改_前缀的文件即视为已修改）"""
    if not os.path.exists(file_dir):
        return False
    for f in os.listdir(file_dir):
        if f.startswith("改_"):
            return True
    return False


def count_corrections_in_dir(dir_path: str) -> int:
    """统计目录下修改文件数量"""
    if not os.path.exists(dir_path):
        return 0
    count = 0
    for f in os.listdir(dir_path):
        if f.startswith("改_"):
            count += 1
    return count


def _cleanup_empty_dirs(start_dir: str):
    """从 start_dir 开始逐层向上删除空目录，直到 upload 根目录。"""
    _dir = start_dir
    while _dir and _dir != get_upload_dir():
        try:
            if not os.listdir(_dir):
                os.rmdir(_dir)
                _dir = os.path.dirname(_dir)
            else:
                break
        except OSError:
            break


def move_content_file(essay, old_dir: str, new_dir: str, filenames=None) -> str:
    """把作文自身的文件集合从旧目录移到新目录。
    filenames：该作文拥有的文件名（content_file + 图片等），缺省时仅移动 content_file。
    只移动指定文件，避免误搬同目录下其它作文的文件。
    返回新的 content_file 值（第一个成功移动文件的相对路径），失败返回空字符串。
    仅当新旧路径不同且旧路径存在时才操作。
    """
    if not old_dir or not new_dir:
        return ""
    if os.path.abspath(old_dir) == os.path.abspath(new_dir):
        return essay.content_file
    if not os.path.isdir(old_dir):
        return ""
    if filenames is None:
        filenames = [os.path.basename(essay.content_file)] if essay.content_file else []

    os.makedirs(new_dir, exist_ok=True)
    moved = []
    for fname in filenames:
        if not fname:
            continue
        src = os.path.join(old_dir, fname)
        dst = os.path.join(new_dir, fname)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.move(src, dst)
                moved.append(fname)
            except OSError:
                pass

    _cleanup_empty_dirs(old_dir)

    if moved:
        return os.path.relpath(os.path.join(new_dir, moved[0]), get_upload_dir())
    return ""


def resize_image_within(content: bytes, max_dim: int = 4000, max_bytes: int = 2 * 1024 * 1024) -> bytes:
    """检查图片宽高是否都在 max_dim 内、体积是否在 max_bytes 内，
    超出则等比例缩小/降质量压缩后返回新字节。未超限时原样返回。"""
    import io
    from PIL import Image

    try:
        with Image.open(io.BytesIO(content)) as im:
            w, h = im.size
            if w <= max_dim and h <= max_dim and len(content) <= max_bytes:
                return content

            fmt = (im.format or "JPEG").upper()

            def _compress(quality, scale=1.0):
                src = im
                if scale < 1.0:
                    tw = max(1, round(w * scale))
                    th = max(1, round(h * scale))
                    src = im.resize((tw, th), Image.LANCZOS)
                buf = io.BytesIO()
                if fmt == "PNG":
                    src.convert("RGB").save(buf, format="JPEG", quality=quality)
                elif fmt == "GIF":
                    src.convert("RGB").save(buf, format="JPEG", quality=quality)
                elif fmt == "WEBP":
                    src.save(buf, format="WEBP", quality=quality)
                else:
                    src.save(buf, format="JPEG", quality=quality)
                return buf.getvalue()

            # 若尺寸超限，先缩到 4000 内
            if w > max_dim or h > max_dim:
                if w >= h:
                    w, h = max_dim, max(1, round(h * max_dim / w))
                else:
                    h, w = max_dim, max(1, round(w * max_dim / h))
                im = im.resize((w, h), Image.LANCZOS)

            # 逐级降质量/降尺寸，直到 ≤ max_bytes
            result = _compress(85)
            for quality, scale in [(75, 1.0), (60, 1.0), (50, 0.9), (40, 0.8)]:
                if len(result) <= max_bytes:
                    break
                result = _compress(quality, scale)
            return result
    except Exception:
        return content
