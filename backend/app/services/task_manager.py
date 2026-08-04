import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

@dataclass
class BatchTask:
    id: str
    type: str  # ocr / ai_correct / ai_rewrite
    status: str = "running"  # running / completed / failed
    total: int = 0
    success: int = 0
    errors: list = field(default_factory=list)
    created_at: float = 0
    message: str = ""

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
        }


_tasks: dict[str, BatchTask] = {}
_lock = threading.Lock()


def create_task(task_id: str, task_type: str, total: int) -> BatchTask:
    task = BatchTask(id=task_id, type=task_type, total=total)
    with _lock:
        _tasks[task_id] = task
    return task


def get_task(task_id: str) -> Optional[dict]:
    with _lock:
        task = _tasks.get(task_id)
        return task.to_dict() if task else None


def update_task(task_id: str, success: int = None, errors: list = None, status: str = None, message: str = None, total: int = None):
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


def cleanup_old_tasks(max_age: float = 3600):
    """清理超过 max_age 秒的已完成任务"""
    now = time.time()
    with _lock:
        expired = [k for k, v in _tasks.items() if v.status != "running" and (now - v.created_at) > max_age]
        for k in expired:
            del _tasks[k]


def run_batch_ocr(task_id: str, essay_ids: list, current_user_id: int, ocr_config: dict, get_db, Essay, _log_operation):
    """在后台线程中执行批量 OCR"""
    from time import sleep
    import json
    import os

    db = next(get_db())
    try:
        essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
        update_task(task_id, total=len(essays))

        xfyun_cfg = ocr_config.get("xfyun", {})
        success = 0
        errors = []

        for i, e in enumerate(essays):
            if e.file_type != "image" or not e.content_file:
                errors.append({"id": e.id, "student": e.student_name, "reason": "非图片类型或无文件"})
                update_task(task_id, success=success, errors=errors)
                continue
            try:
                essay_dir = os.path.dirname(os.path.join(_get_upload_dir(db), e.content_file))
                from ..utils.ocr_utils import ocr_essay_images
                text = ocr_essay_images(essay_dir, xfyun_cfg)
                e.content_text = text
                _log_operation(db, e.id, current_user_id, "OCR", "批量 OCR 识别完成")
                success += 1
            except Exception as ex:
                errors.append({"id": e.id, "student": e.student_name, "reason": str(ex)})
            update_task(task_id, success=success, errors=errors)
            sleep(0.1)

        db.commit()
        update_task(task_id, status="completed" if not errors else "failed", message=f"完成 {success}/{len(essays)}")
    except Exception as ex:
        update_task(task_id, status="failed", message=str(ex))
    finally:
        db.close()


def run_batch_ai_correct(task_id: str, essay_ids: list, current_user_id: int, llm_cfg: dict, get_db, Essay, _log_operation):
    from time import sleep

    db = next(get_db())
    try:
        essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
        update_task(task_id, total=len(essays))

        from ..utils.ocr_utils import ai_correct_text
        success = 0
        errors = []

        for i, e in enumerate(essays):
            if not e.content_text or not e.content_text.strip():
                errors.append({"id": e.id, "student": e.student_name, "reason": "无文字内容"})
                update_task(task_id, success=success, errors=errors)
                continue
            try:
                result = ai_correct_text(e.content_text, llm_cfg)
                corrected_text = result.get("修改后内容", e.content_text)
                e.content_text = corrected_text
                if not e.essay_title or not e.essay_title.strip():
                    title = result.get("作文标题", "")
                    if title and title != "未知":
                        e.essay_title = title.strip()
                _log_operation(db, e.id, current_user_id, "编辑", "批量 AI 错别字修正")
                success += 1
            except Exception as ex:
                errors.append({"id": e.id, "student": e.student_name, "reason": str(ex)})
            update_task(task_id, success=success, errors=errors)
            sleep(0.1)

        db.commit()
        update_task(task_id, status="completed" if not errors else "failed", message=f"完成 {success}/{len(essays)}")
    except Exception as ex:
        update_task(task_id, status="failed", message=str(ex))
    finally:
        db.close()


def run_batch_ai_rewrite(task_id: str, essay_ids: list, current_user_id: int, llm_cfg: dict, get_db, Essay, _log_operation):
    from time import sleep
    from datetime import datetime

    db = next(get_db())
    try:
        essays = db.query(Essay).filter(Essay.id.in_(essay_ids), Essay.deleted_at == None).all()
        update_task(task_id, total=len(essays))

        from ..utils.ocr_utils import ai_rewrite_text
        success = 0
        errors = []

        for i, e in enumerate(essays):
            if not e.content_text or not e.content_text.strip():
                errors.append({"id": e.id, "student": e.student_name, "reason": "无文字内容"})
                update_task(task_id, success=success, errors=errors)
                continue
            try:
                rewritten = ai_rewrite_text(e.content_text, llm_cfg, prompt_template=llm_cfg.get("prompt"))
                e.corrected_text = rewritten
                if e.status == "pending" and e.content_text and e.content_text.strip():
                    e.status = "confirming"
                e.corrected_at = datetime.now()
                e.reviewer_id = current_user_id
                _log_operation(db, e.id, current_user_id, "批改", "批量 AI 改写")
                success += 1
            except Exception as ex:
                errors.append({"id": e.id, "student": e.student_name, "reason": str(ex)})
            update_task(task_id, success=success, errors=errors)
            sleep(0.1)

        db.commit()
        update_task(task_id, status="completed" if not errors else "failed", message=f"完成 {success}/{len(essays)}")
    except Exception as ex:
        update_task(task_id, status="failed", message=str(ex))
    finally:
        db.close()


def _get_upload_dir(db):
    from ..database import SessionLocal
    from ..utils.file_utils import get_upload_dir as _f_get_upload_dir
    return _f_get_upload_dir()
