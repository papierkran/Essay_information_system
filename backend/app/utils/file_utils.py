import os
import shutil
import json
from datetime import datetime

_SETTINGS = None


def _load_settings():
    global _SETTINGS
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path) as f:
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
) -> str:
    """生成作文存储目录路径。
    - 有任务：{年}/{MMDD}_{课程名}/{年级}{方式}第{N}次/{学生}/
    - 无任务：{年}/{月}月/{日}/{年级}{方式}第{N}次/{学生}/
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


def move_content_file(essay, old_dir: str, new_dir: str) -> str:
    """把作文文件从旧目录移到新目录。
    返回新的 content_file 值（新目录下第一个文件的相对路径），失败返回空字符串。
    仅当新旧路径不同且旧路径存在时才操作。
    """
    if not old_dir or not new_dir:
        return ""
    if os.path.abspath(old_dir) == os.path.abspath(new_dir):
        return essay.content_file
    if not os.path.isdir(old_dir):
        return ""

    os.makedirs(new_dir, exist_ok=True)
    first_file = ""
    for fname in os.listdir(old_dir):
        src = os.path.join(old_dir, fname)
        dst = os.path.join(new_dir, fname)
        if os.path.exists(dst):
            continue
        shutil.move(src, dst)
        if not first_file:
            first_file = fname

    # 清理空目录（逐层向上删）
    _dir = old_dir
    while _dir != get_upload_dir():
        try:
            if not os.listdir(_dir):
                os.rmdir(_dir)
                _dir = os.path.dirname(_dir)
            else:
                break
        except OSError:
            break

    if first_file:
        return os.path.relpath(os.path.join(new_dir, first_file), get_upload_dir())
    return ""
