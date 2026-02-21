from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    STUDENT = "student"
    PROFESSOR = "professor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)

    enrollments = relationship("Enrollment", back_populates="user")
    sessions = relationship("LearningSession", back_populates="user")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, index=True)
    description = Column(Text)
    professor_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    professor = relationship("User", foreign_keys=[professor_id])
    enrollments = relationship("Enrollment", back_populates="course")
    sessions = relationship("LearningSession", back_populates="course")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50), default="student")

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)

    user = relationship("User", back_populates="sessions")
    course = relationship("Course", back_populates="sessions")
    cognitive_records = relationship("CognitiveRecord", back_populates="session")


class CognitiveRecord(Base):
    __tablename__ = "cognitive_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    cognitive_load = Column(Float, default=0.5)
    attention_level = Column(Float, default=0.5)
    engagement = Column(Float, default=0.5)
    confusion_indicator = Column(Float, default=0.0)
    fatigue_indicator = Column(Float, default=0.0)

    raw_data = Column(JSON, nullable=True)

    session = relationship("LearningSession", back_populates="cognitive_records")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    directives = Column(JSON, nullable=True)
    cognitive_state = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Calibration(Base):
    __tablename__ = "calibrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), nullable=True)

    baseline_cognitive_load = Column(Float)
    baseline_attention = Column(Float)
    baseline_engagement = Column(Float)

    calibration_duration_seconds = Column(Integer)
    performed_at = Column(DateTime, default=datetime.utcnow)
