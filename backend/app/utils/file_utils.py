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


def get_essay_dir(
    year: str,
    month: str,
    day: str,
    grade: str,
    essay_number: int,
    collector_name: str,
    student_name: str = "",
    teaching_mode: str = "",
) -> str:
    """生成作文存储目录路径"""
    grade_name = grade if grade else "未定年级"
    if teaching_mode:
        grade_name = f"{grade_name}{teaching_mode}"
    path = os.path.join(
        get_upload_dir(),
        year,
        month,
        day,
        f"{grade_name}第{essay_number}次",
    )
    if student_name:
        path = os.path.join(path, student_name)
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
    rm = f"_{remark}" if remark else ""
    safe_title = essay_title.replace("/", "_").replace("\\", "_") if essay_title else "无标题"
    return f"{safe_title}_{student_name}_第{essay_number}次_{suppl}{rm}_{timestamp}{ext}"


def generate_correction_filename(original_filename: str) -> str:
    """生成批改文件名（加 改_ 前缀）"""
    return f"改_{original_filename}"


def has_correction(file_dir: str, original_filename: str) -> bool:
    """判断目录下是否有批改文件（有改_前缀的文件即视为已批改）"""
    if not os.path.exists(file_dir):
        return False
    for f in os.listdir(file_dir):
        if f.startswith("改_"):
            return True
    return False


def count_corrections_in_dir(dir_path: str) -> int:
    """统计目录下批改文件数量"""
    if not os.path.exists(dir_path):
        return 0
    count = 0
    for f in os.listdir(dir_path):
        if f.startswith("改_"):
            count += 1
    return count
