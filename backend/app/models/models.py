from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    desc = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    users = relationship("User", back_populates="organization")
    classes = relationship("Class", back_populates="organization")


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
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    organization = relationship("Organization", back_populates="users")
    user_classes = relationship("UserClass", back_populates="user")
    collected_essays = relationship("Essay", back_populates="collector",
                                    foreign_keys="Essay.collected_by")
    reviewed_essays = relationship("Essay", back_populates="reviewer",
                                   foreign_keys="Essay.reviewer_id")


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    organization = relationship("Organization", back_populates="classes")
    user_classes = relationship("UserClass", back_populates="class_")
    essays = relationship("Essay", back_populates="class_")


class UserClass(Base):
    __tablename__ = "user_classes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    role_in_class = Column(String(20), default="collector")

    user = relationship("User", back_populates="user_classes")
    class_ = relationship("Class", back_populates="user_classes")


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
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
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class_ = relationship("Class", back_populates="essays")
    collector = relationship("User", back_populates="collected_essays",
                             foreign_keys=[collected_by])
    reviewer = relationship("User", back_populates="reviewed_essays",
                            foreign_keys=[reviewer_id])
