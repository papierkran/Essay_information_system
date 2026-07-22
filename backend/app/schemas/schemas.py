from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    grade: str
    essay_number: int
    essay_title: str
    student_name: str
    is_supplement: bool
    teaching_mode: str = "线下"
    remark: str
    content_text: str
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

    class Config:
        from_attributes = True
