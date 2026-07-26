from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ===== 作文收集任务 =====
class TaskCreate(BaseModel):
    name: str
    grade: str
    essay_number: int = 1
    essay_topic: str = ""
    course_name: str = ""
    teaching_mode: str = "线下"
    deadline: Optional[datetime] = None
    is_active: bool = False


class TaskOut(BaseModel):
    id: int
    name: str
    grade: str
    essay_number: int
    essay_topic: str
    course_name: str
    teaching_mode: str
    deadline: Optional[datetime] = None
    is_active: bool
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
    org_id: Optional[int] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str
    phone: str
    role: str
    org_id: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ===== 培训班 =====
class OrganizationCreate(BaseModel):
    name: str
    desc: str = ""


class OrganizationOut(BaseModel):
    id: int
    name: str
    desc: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 班级 =====
class ClassCreate(BaseModel):
    org_id: int
    name: str


class ClassOut(BaseModel):
    id: int
    org_id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 作文 =====
class EssayCreate(BaseModel):
    class_id: int
    task_id: Optional[int] = None
    grade: str = ""
    essay_number: int = 1
    essay_title: str = ""
    student_name: str
    is_supplement: bool = False
    teaching_mode: str = "线下"
    remark: str = ""
    content_text: str = ""


class EssayOut(BaseModel):
    id: int
    class_id: int
    class_name: str = ""
    task_id: Optional[int] = None
    task_name: str = ""
    grade: str
    essay_number: int
    essay_title: str
    student_name: str
    is_supplement: bool
    teaching_mode: str = "线下"
    remark: str
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


class OperationLogOut(BaseModel):
    id: int
    essay_id: int
    user_id: int
    user_name: str = ""
    action: str
    detail: str = ""
    student_name: str = ""
    essay_title: str = ""
    essay_number: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
