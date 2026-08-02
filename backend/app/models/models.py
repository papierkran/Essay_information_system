from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index, UniqueConstraint, CheckConstraint, Enum as SAEnum
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
    course_name = Column(String(100), default="")  # 课程名称
    teaching_mode = Column(String(10), default="线下")  # 线下/线上
    deadline = Column(DateTime, nullable=True)  # 收集截止时间
    is_active = Column(Boolean, default=False)  # 是否为当前活跃任务
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    essays = relationship("Essay", back_populates="task", primaryjoin="and_(Essay.task_id==EssayTask.id, Essay.deleted_at==None)")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    desc = Column(Text, default="")
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    users = relationship("User", back_populates="organization", primaryjoin="and_(User.org_id==Organization.id, User.deleted_at==None)")
    classes = relationship("Class", back_populates="organization", primaryjoin="and_(Class.org_id==Organization.id, Class.deleted_at==None)")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    nickname = Column(String(50), default="")
    phone = Column(String(20), default="")
    role = Column(String(50), default="collector")  # admin / collector / reviewer
    org_id = Column(Integer, ForeignKey("organizations.id"))
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    organization = relationship("Organization", back_populates="users")
    user_classes = relationship("UserClass", back_populates="user", primaryjoin="and_(UserClass.user_id==User.id, UserClass.deleted_at==None)")
    collected_essays = relationship("Essay", back_populates="collector",
                                    foreign_keys="Essay.collected_by",
                                    primaryjoin="and_(Essay.collected_by==User.id, Essay.deleted_at==None)")
    reviewed_essays = relationship("Essay", back_populates="reviewer",
                                   foreign_keys="Essay.reviewer_id",
                                   primaryjoin="and_(Essay.reviewer_id==User.id, Essay.deleted_at==None)")


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    name = Column(String(100), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    organization = relationship("Organization", back_populates="classes")
    user_classes = relationship("UserClass", back_populates="class_", primaryjoin="and_(UserClass.class_id==Class.id, UserClass.deleted_at==None)")
    essays = relationship("Essay", back_populates="class_", primaryjoin="and_(Essay.class_id==Class.id, Essay.deleted_at==None)")


class UserClass(Base):
    __tablename__ = "user_classes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    role_in_class = Column(String(20), default="collector")
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "class_id", "role_in_class", name="uq_user_class_role"),
    )

    user = relationship("User", back_populates="user_classes")
    class_ = relationship("Class", back_populates="user_classes")


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("essay_tasks.id"), nullable=True)  # 关联收集任务
    grade = Column(String(20), default="")
    essay_number = Column(Integer, default=1)
    essay_title = Column(String(200), default="")
    student_name = Column(String(50), nullable=False)
    is_supplement = Column(Boolean, default=False)
    teaching_mode = Column(String(10), default="线下")  # 线下/线上
    remark = Column(Text, default="")
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
        UniqueConstraint("class_id", "task_id", "student_name", "essay_number", "is_supplement", "essay_title",
                         name="uq_essay_task_student"),
        CheckConstraint(
            "status IN ('pending', 'confirming', 'corrected')",
            name="ck_essays_status",
        ),
    )

    class_ = relationship("Class", back_populates="essays")
    task = relationship("EssayTask", back_populates="essays")
    collector = relationship("User", back_populates="collected_essays",
                             foreign_keys=[collected_by])
    reviewer = relationship("User", back_populates="reviewed_essays",
                            foreign_keys=[reviewer_id])
    operations = relationship("OperationLog", back_populates="essay",
                              primaryjoin="and_(OperationLog.essay_id==Essay.id, Essay.deleted_at==None)")


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
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_operation_logs_essay_id", "essay_id"),
        Index("idx_operation_logs_created_at", "created_at"),
        Index("idx_operation_logs_user_id", "user_id"),
    )

    essay = relationship("Essay", back_populates="operations", foreign_keys=[essay_id])
    user = relationship("User", foreign_keys=[user_id])
