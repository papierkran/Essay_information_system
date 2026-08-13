import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 3

@dataclass
class BatchTask:
    id: str
    type: str  # ocr / ai_correct / ai_rewrite / pipeline
    status: str = "running"  # running / completed / failed
    total: int = 0
    success: int = 0
    errors: list = field(default_factory=list)
    created_at: float = 0
    message: str = ""
    current: str = ""  # 正在处理的作文
    stage: str = ""  # 当前步骤

    def __post_init__(self):
        self.created_at = time.time()

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "total": self.total,
            "success": self.success,
            "errors": self.errors,
            "message": self.message,
            "current": self.current,
            "stage": self.stage,
        }


_tasks: dict[str, BatchTask] = {}
_lock = threading.Lock()


def create_task(task_id: str, task_type: str, total: int, status: str = "running") -> BatchTask:
    task = BatchTask(id=task_id, type=task_type, total=total, status=status)
    with _lock:
        _tasks[task_id] = task
    return task


def get_task(task_id: str) -> Optional[dict]:
    with _lock:
        task = _tasks.get(task_id)
        return task.to_dict() if task else None


def update_task(task_id: str, success: int = None, errors: list = None, status: str = None, message: str = None, total: int = None, current: str = None, stage: str = None):
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        if success is not None:
            task.success = success
        if errors is not None:
            task.errors = errors
        if status is not None:
            task.status = status
        if message is not None:
            task.message = message
        if total is not None:
            task.total = total
        if current is not None:
            task.current = current
        if stage is not None:
            task.stage = stage


def cleanup_old_tasks(max_age: float = 3600):
    """清理超过 max_age 秒的已完成任务"""
    now = time.time()
    with _lock:
        expired = [k for k, v in _tasks.items() if v.status != "running" and (now - v.created_at) > max_age]
        for k in expired:
            del _tasks[k]


def run_batch_ocr(task_id: str, essay_ids: list, current_user_id: int, ocr_config: dict, get_db, Essay, _log_operation):
    """在后台线程中执行批量 OCR（线程池并发，每篇独立 session）"""
    import os
    from ..utils.ocr_utils import ocr_essay_images_with_fallback

    xfyun_cfg = ocr_config.get("xfyun", {})

    def worker(sdb, e):
        if e.file_type != "image" or not e.content_file:
            raise RuntimeError("非图片类型或无文件")
        essay_dir = os.path.dirname(os.path.join(_get_upload_dir(sdb), e.content_file))
        meta = {}
        text = ocr_essay_images_with_fallback(sdb, e.id, essay_dir, xfyun_cfg, meta=meta)
        e.content_text = text
        op_text = "批量 OCR 识别完成"
        if meta.get("image_corrected"):
            op_text += f"（图片矫正 {meta['image_corrected']} 张，最大旋转 {meta['max_rotation']:.1f}°）"
        _log_operation(sdb, e.id, current_user_id, "OCR", op_text)

    _run_batch_parallel(task_id, essay_ids, worker, get_db, Essay, "OCR识别")


def _run_batch_parallel(task_id, essay_ids, worker_fn, get_db, Essay, stage_label):
    """用线程池(MAX_WORKERS)并发处理 essay_ids，每篇独立 DB session"""
    from ..database import SessionLocal

    db = next(get_db())
    try:
        essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
    finally:
        db.close()

    total = len(essays)
    update_task(task_id, total=total)

    stats_lock = threading.Lock()
    success = 0
    errors = []
    active = set()  # 正在处理的学生名

    def process(essay_id, name):
        nonlocal success
        sdb = SessionLocal()
        try:
            e = sdb.query(Essay).filter(Essay.id == essay_id).first()
            if e is None:
                raise RuntimeError("作文不存在")
            worker_fn(sdb, e)
            sdb.commit()
            with stats_lock:
                success += 1
        except Exception as ex:
            sdb.rollback()
            with stats_lock:
                errors.append({"id": essay_id, "student": name, "reason": str(ex)})
        finally:
            with stats_lock:
                active.discard(name)
                update_task(task_id, success=success, errors=list(errors), current="、".join(sorted(active)[-3:]) or "", stage=stage_label)
            sdb.close()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = []
        for e in essays:
            name = e.student_name
            with stats_lock:
                active.add(name)
                update_task(task_id, success=success, errors=list(errors), current="、".join(sorted(active)[-3:]) or "", stage=stage_label)
            futs.append(pool.submit(process, e.id, name))
        for f in as_completed(futs):
            try:
                f.result()
            except Exception:
                pass

    update_task(task_id, status="completed" if not errors else "failed", message=f"完成 {success}/{total}")


def run_batch_ai_correct(task_id: str, essay_ids: list, current_user_id: int, llm_cfg: dict, get_db, Essay, _log_operation):
    from ..utils.ocr_utils import ai_correct_text

    def worker(sdb, e):
        if not e.content_text or not e.content_text.strip():
            raise RuntimeError("无文字内容")
        essay_info = {
            "student_name": e.student_name,
            "grade": e.grade,
            "essay_number": e.essay_number,
            "essay_title": e.essay_title,
            "teaching_mode": e.teaching_mode,
            "task_name": e.task.name if e.task else None,
        }
        result = ai_correct_text(e.content_text, llm_cfg, essay_info=essay_info)
        corrected_text = result.get("修改后内容", e.content_text)
        e.content_text = corrected_text
        if not e.essay_title or not e.essay_title.strip():
            title = result.get("作文标题", "")
            if title and title != "未知":
                e.essay_title = title.strip()
        _log_operation(sdb, e.id, current_user_id, "编辑", "批量 AI 错别字修正")

    _run_batch_parallel(task_id, essay_ids, worker, get_db, Essay, "AI错别字修正")


def run_batch_ai_rewrite(task_id: str, essay_ids: list, current_user_id: int, llm_cfg: dict, get_db, Essay, _log_operation):
    from datetime import datetime
    from ..utils.ocr_utils import ai_rewrite_text

    def worker(sdb, e):
        if not e.content_text or not e.content_text.strip():
            raise RuntimeError("无文字内容")
        rewritten = ai_rewrite_text(e.content_text, llm_cfg, prompt_template=llm_cfg.get("prompt"))
        e.corrected_text = rewritten
        if e.status in ("pending", "rework") and e.content_text and e.content_text.strip():
            e.status = "confirming"
        e.corrected_at = datetime.now()
        e.reviewer_id = current_user_id
        _log_operation(sdb, e.id, current_user_id, "批改", "批量 AI 改写")

    _run_batch_parallel(task_id, essay_ids, worker, get_db, Essay, "AI一键修改")


def _get_upload_dir(db):
    from ..database import SessionLocal
    from ..utils.file_utils import get_upload_dir as _f_get_upload_dir
    return _f_get_upload_dir()


def run_batch_pipeline(ocr_task_id: str, correct_task_id: str, rewrite_task_id: str, essay_ids: list, current_user_id: int, ocr_config: dict, typo_cfg: dict, editor_cfg: dict, get_db, Essay, _log_operation):
    """后台流水线：OCR → AI错别字修正 → AI一键修改，三个阶段各自独立任务卡片"""
    from datetime import datetime
    import os
    from ..utils.ocr_utils import ocr_essay_images_with_fallback, ai_correct_text, ai_rewrite_text

    def ocr_worker(sdb, e):
        if (not e.content_text or not e.content_text.strip()) and e.file_type == "image" and e.content_file:
            essay_dir = os.path.dirname(os.path.join(_get_upload_dir(sdb), e.content_file))
            meta = {}
            text = ocr_essay_images_with_fallback(sdb, e.id, essay_dir, ocr_config.get("xfyun", {}), meta=meta)
            e.content_text = text
            op_text = "流水线 OCR 识别完成"
            if meta.get("image_corrected"):
                op_text += f"（图片矫正 {meta['image_corrected']} 张，最大旋转 {meta['max_rotation']:.1f}°）"
            _log_operation(sdb, e.id, current_user_id, "OCR", op_text)
        elif not e.content_text or not e.content_text.strip():
            raise RuntimeError("无文字内容")

    def correct_worker(sdb, e):
        if not e.content_text or not e.content_text.strip():
            raise RuntimeError("无文字内容")
        essay_info = {
            "student_name": e.student_name,
            "grade": e.grade,
            "essay_number": e.essay_number,
            "essay_title": e.essay_title,
            "teaching_mode": e.teaching_mode,
            "task_name": e.task.name if e.task else None,
        }
        result = ai_correct_text(e.content_text, typo_cfg, essay_info=essay_info)
        corrected_text = result.get("修改后内容", e.content_text)
        e.content_text = corrected_text
        if not e.essay_title or not e.essay_title.strip():
            title = result.get("作文标题", "")
            if title and title != "未知":
                e.essay_title = title.strip()
        _log_operation(sdb, e.id, current_user_id, "编辑", "流水线 AI 错别字修正")

    def rewrite_worker(sdb, e):
        if not e.content_text or not e.content_text.strip():
            raise RuntimeError("无文字内容")
        rewritten = ai_rewrite_text(e.content_text, editor_cfg, prompt_template=editor_cfg.get("prompt"))
        e.corrected_text = rewritten
        if e.status in ("pending", "rework"):
            e.status = "confirming"
        e.corrected_at = datetime.now()
        e.reviewer_id = current_user_id
        _log_operation(sdb, e.id, current_user_id, "批改", "流水线 AI 修改")

    try:
        update_task(ocr_task_id, status="running")
        _run_batch_parallel(ocr_task_id, essay_ids, ocr_worker, get_db, Essay, "OCR识别")
        update_task(correct_task_id, status="running")
        _run_batch_parallel(correct_task_id, essay_ids, correct_worker, get_db, Essay, "AI错别字修正")
        update_task(rewrite_task_id, status="running")
        _run_batch_parallel(rewrite_task_id, essay_ids, rewrite_worker, get_db, Essay, "AI一键修改")
    except Exception as ex:
        update_task(rewrite_task_id, status="failed", message=str(ex))
