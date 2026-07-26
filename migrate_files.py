# -*- coding: utf-8 -*-
"""文件目录迁移：按新规则重组 /root/桌面/作文/ 下的文件目录。
- 有 task_id → {MMDD}_{课程名}/{年级}{方式}第{N}次/{学生}/
- 无 task_id → 保持原路径 {年}/{月}月/{日}/{年级}{方式}第{N}次/{学生}/
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import SessionLocal
from backend.app.models.models import Essay, EssayTask
from backend.app.utils.file_utils import get_upload_dir

db = SessionLocal()
base = get_upload_dir()

essays = db.query(Essay).filter(
    Essay.deleted_at == None,
    Essay.content_file != "",
).all()

moved = 0
skipped = 0
errors = 0

for essay in essays:
    if not essay.content_file:
        continue

    old_rel = essay.content_file
    old_full = os.path.join(base, old_rel)
    if not os.path.exists(old_full):
        skipped += 1
        continue

    task_name = ""
    task_created_at = None
    if essay.task_id:
        task = db.query(EssayTask).filter(EssayTask.id == essay.task_id).first()
        if task:
            task_name = task.name
            task_created_at = task.created_at

    # 构建新路径（仅当有 task_id 时才迁移）
    if not essay.task_id:
        skipped += 1
        continue

    task = db.query(EssayTask).filter(EssayTask.id == essay.task_id).first()
    if not task:
        skipped += 1
        continue

    grade = essay.grade or "未定年级"
    mode = essay.teaching_mode or ""
    grade_name = f"{grade}{mode}" if mode else grade
    task_dir_seg = f"{grade_name}第{essay.essay_number}次"

    mmdd = task.created_at.strftime("%m%d")
    task_year = str(task.created_at.year)
    course = task.name.replace("/", "_").replace("\\", "_")
    new_rel_dir = os.path.join(task_year, f"{mmdd}_{course}", task_dir_seg, essay.student_name)

    new_dir = os.path.join(base, new_rel_dir)

    # 如果新旧路径相同，跳过
    old_dir = os.path.dirname(old_full)
    if os.path.abspath(old_dir) == os.path.abspath(new_dir):
        skipped += 1
        continue

    try:
        os.makedirs(new_dir, exist_ok=True)

        # 移动目录下所有文件
        anything_moved = False
        if os.path.isdir(old_dir) and os.path.abspath(old_dir) != os.path.abspath(new_dir):
            for fname in os.listdir(old_dir):
                src = os.path.join(old_dir, fname)
                dst = os.path.join(new_dir, fname)
                if os.path.exists(dst):
                    # 目标已存在，跳过
                    continue
                os.rename(src, dst)
                anything_moved = True

            # 清理空目录
            if anything_moved and not os.listdir(old_dir):
                os.rmdir(old_dir)

        if anything_moved:
            # 更新 content_file 为新路径（取目录中第一个文件作为 content_file）
            new_files = os.listdir(new_dir)
            if new_files:
                new_content_file = os.path.relpath(os.path.join(new_dir, new_files[0]), base)
                essay.content_file = new_content_file
            moved += 1
        else:
            skipped += 1
    except Exception as e:
        print(f"❌ {essay.student_name}: {e}")
        errors += 1

db.commit()
db.close()

print(f"\n迁移完成: 移动 {moved} 条, 跳过 {skipped} 条, 错误 {errors} 条")

# 清理空目录
print("\n清理空目录...")
for root, dirs, files in os.walk(base, topdown=False):
    for d in dirs:
        dpath = os.path.join(root, d)
        try:
            if not os.listdir(dpath):
                os.rmdir(dpath)
                print(f"  删除空目录: {os.path.relpath(dpath, base)}")
        except OSError:
            pass
print("完成。")
