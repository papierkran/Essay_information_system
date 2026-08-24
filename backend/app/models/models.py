from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index, UniqueConstraint, CheckConstraint, Enum as SAEnum, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class ActionEnum(str, enum.Enum):
    """操作类型枚举"""
    CREATE = "创建"
    UPDATE = "修改"
    DELETE = "删除"
    RECOVER = "恢复"
    EDIT = "编辑"
    UPLOAD = "上传"
    CORRECT = "批改"
    OCR = "OCR"
    _legacy_edit = "EDIT"
    _legacy_correct = "CORRECT"


class EssayTask(Base):
    """作文收集任务"""
    __tablename__ = "essay_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 任务名称
    grade = Column(String(20), nullable=False)  # 年级
    essay_number = Column(Integer, default=1)  # 第几次作文
    essay_topic = Column(String(200), default="")  # 文章主题
    course_id = Column(Integer, ForeignKey("course.id"), nullable=True)  # 关联课程
    teaching_mode = Column(String(10), default="线下")  # 线下/线上
    start_time = Column(DateTime, nullable=True)  # 收集开始时间
    deadline = Column(DateTime, nullable=True)  # 收集截止时间
    is_active = Column(Boolean, default=False)  # 是否为当前活跃任务
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    course = relationship("Course")

    @property
    def course_name(self) -> str:
        return self.course.name if self.course else ""

    essays = relationship("Essay", back_populates="task", primaryjoin="and_(Essay.task_id==EssayTask.id, Essay.deleted_at==None)")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    nickname = Column(String(50), default="")
    phone = Column(String(20), default="")
    role = Column(String(50), default="collector")  # admin / collector / reviewer
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    collected_essays = relationship("Essay", back_populates="collector",
                                    foreign_keys="Essay.collected_by",
                                    primaryjoin="and_(Essay.collected_by==User.id, Essay.deleted_at==None)")
    reviewed_essays = relationship("Essay", back_populates="reviewer",
                                   foreign_keys="Essay.reviewer_id",
                                   primaryjoin="and_(Essay.reviewer_id==User.id, Essay.deleted_at==None)")


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    grade = Column(Text, default="")  # 年级（可选，JSON数组，如 ["初三","高一"]）
    classin_id = Column(String(50), default="")  # ClassIn 班级 ID
    start_date = Column(DateTime, nullable=True)  # 开课时间（可选）
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    essays = relationship("Essay", back_populates="course",
                          foreign_keys="Essay.course_id",
                          primaryjoin="and_(Essay.course_id==Course.id, Essay.deleted_at==None)")


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("essay_tasks.id"), nullable=True)  # 关联收集任务
    course_id = Column(Integer, ForeignKey("course.id"), nullable=True)  # 直接关联课程
    grade = Column(String(20), default="")
    essay_number = Column(Integer, default=1)
    essay_title = Column(String(200), default="")  # 修改前标题
    corrected_title = Column(String(200), default="")  # 修改后标题
    student_name = Column(String(50), nullable=False)
    is_supplement = Column(Boolean, default=False)
    teaching_mode = Column(String(10), default="线下")  # 线下/线上
    remark = Column(Text, default="")
    collector_note = Column(Text, default="")   # 收集者备注
    reviewer_note = Column(Text, default="")    # 批改者备注
    content_text = Column(Text, default="")
    content_file = Column(String(500), default="")
    file_type = Column(String(10), default="text")
    collected_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")
    file_saved = Column(Boolean, default=True)
    corrected_text = Column(Text, default="")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    corrected_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_essays_status", "status"),
        Index("idx_essays_collected_by", "collected_by"),
        Index("idx_essays_grade", "grade"),
        Index("idx_essays_created_at", "created_at"),
        Index("idx_essays_task_id", "task_id"),
        Index("idx_essays_deleted_at", "deleted_at"),
        UniqueConstraint("task_id", "student_name", "essay_number", "is_supplement", "essay_title",
                         name="uq_essay_task_student"),
        CheckConstraint(
            "status IN ('pending', 'confirming', 'corrected', 'rework')",
            name="ck_essays_status",
        ),
    )

    course = relationship("Course", back_populates="essays", foreign_keys=[course_id])
    task = relationship("EssayTask", back_populates="essays")
    collector = relationship("User", back_populates="collected_essays",
                             foreign_keys=[collected_by])
    reviewer = relationship("User", back_populates="reviewed_essays",
                            foreign_keys=[reviewer_id])
    operations = relationship("OperationLog", back_populates="essay",
                              primaryjoin="and_(OperationLog.essay_id==Essay.id, Essay.deleted_at==None)")


class EssayImage(Base):
    __tablename__ = "essay_images"

    id = Column(Integer, primary_key=True, index=True)
    essay_id = Column(Integer, ForeignKey("essays.id"), nullable=False, index=True)
    filename = Column(String(200), nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    essay = relationship("Essay", backref="images")


class SystemConfig(Base):
    """系统配置（OCR、LLM 等），按 key 存储 JSON value"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, default="{}")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    essay_id = Column(Integer, ForeignKey("essays.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(SAEnum(ActionEnum, values_callable=lambda x: [e.value for e in x]), nullable=False)
    old_value = Column(Text, default="")  # 变更前的值（JSON格式）
    new_value = Column(Text, default="")  # 变更后的值（JSON格式）
    detail = Column(String(500), default="")
    batch_id = Column(String(50), nullable=True)   # 批量操作分组ID
    essay_ids = Column(Text, nullable=True)        # 批量操作涉及的作文ID列表（JSON数组）
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_operation_logs_essay_id", "essay_id"),
        Index("idx_operation_logs_created_at", "created_at"),
        Index("idx_operation_logs_user_id", "user_id"),
        Index("idx_operation_logs_batch_id", "batch_id"),
        Index("idx_operation_logs_user_created", "user_id", "created_at"),
    )

    essay = relationship("Essay", back_populates="operations", foreign_keys=[essay_id])
    user = relationship("User", foreign_keys=[user_id])
