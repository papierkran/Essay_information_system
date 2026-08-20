from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ===== 作文收集任务 =====
class TaskCreate(BaseModel):
    name: str
    grade: str = ""
    essay_number: Optional[int] = None
    essay_topic: str = ""
    course_id: Optional[int] = None
    teaching_mode: str = "线下"
    start_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    is_active: bool = False


class TaskOut(BaseModel):
    id: int
    name: str
    grade: str
    essay_number: int
    essay_topic: str
    course_id: Optional[int] = None
    course_name: str
    teaching_mode: str
    start_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    is_active: bool
    submitted_count: int = 0
    pending_count: int = 0
    corrected_count: int = 0
    rework_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 密码修改 =====
class PasswordChange(BaseModel):
    old_password: str
    new_password: str


# ===== 用户 =====
class UserCreate(BaseModel):
    username: str = ""
    password: str = ""
    nickname: str = ""
    phone: str = ""
    role: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str
    phone: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ===== 课程 =====
class CourseCreate(BaseModel):
    name: str
    grade: str = ""
    classin_id: str = ""
    start_date: Optional[datetime] = None


class CourseOut(BaseModel):
    id: int
    name: str
    grade: str = ""
    classin_id: str = ""
    start_date: Optional[datetime] = None
    created_at: datetime
    task_count: int = 0
    essay_count: int = 0

    class Config:
        from_attributes = True


# ===== 作文 =====
class EssayCreate(BaseModel):
    task_id: Optional[int] = None
    course_id: Optional[int] = None
    grade: str = ""
    essay_number: int = 1
    essay_title: str = ""
    corrected_title: str = ""
    student_name: str
    is_supplement: bool = False
    teaching_mode: str = "线下"
    remark: str = ""
    collector_note: str = ""
    content_text: str = ""


class EssayOut(BaseModel):
    id: int
    task_id: Optional[int] = None
    task_name: str = ""
    course_id: Optional[int] = None
    course_name: str = ""
    grade: str
    essay_number: int
    essay_title: str
    corrected_title: str = ""
    student_name: str
    is_supplement: bool
    teaching_mode: str = "线下"
    remark: str
    collector_note: str = ""
    reviewer_note: str = ""
    content_text: str
    corrected_text: str = ""
    content_file: str
    file_type: str
    collected_by: int
    collector_name: str = ""
    status: str
    reviewer_id: Optional[int] = None
    reviewer_name: str = ""
    corrected_at: Optional[datetime] = None
    created_at: datetime
    file_path: str = ""
    has_correction: bool = False
    file_saved: bool = True
    word_count: int = 0
    corrected_word_count: int = 0

    class Config:
        from_attributes = True


class SystemConfigOut(BaseModel):
    config_key: str
    config_value: dict
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemConfigUpdate(BaseModel):
    config_key: str
    config_value: dict


class OperationLogOut(BaseModel):
    id: int
    essay_id: Optional[int] = None
    user_id: int
    user_name: str = ""
    action: str
    old_value: str = ""
    new_value: str = ""
    detail: str = ""
    batch_id: Optional[str] = None
    essay_ids: Optional[str] = None
    student_name: str = ""
    essay_title: str = ""
    corrected_title: str = ""
    essay_number: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
