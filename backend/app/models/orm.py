from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column

Base: Any = declarative_base()

# Use JSONB for PostgreSQL, JSON for MySQL
JSONType = JSONB().with_variant(JSON, "mysql")


class UserORM(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), server_default="user", nullable=False)

    __table_args__ = (Index("ix_users_role", "role"),)


class QuestionORM(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # easy/medium/hard
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    company_tags: Mapped[Any] = mapped_column(JSONType, default=list, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    starter_code: Mapped[Any] = mapped_column(
        JSONType, default=dict, nullable=False
    )  # {"python": "...", "javascript": "..."}
    examples: Mapped[Any] = mapped_column(JSONType, default=list, nullable=False)
    test_cases: Mapped[Any] = mapped_column(JSONType, default=list, nullable=False)
    hints: Mapped[Any] = mapped_column(JSONType, default=list, nullable=False)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_complexity: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    space_complexity: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    constraints: Mapped[Any] = mapped_column(JSONType, default=list, nullable=False)
    is_interactive: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_status: Mapped[Any] = mapped_column(
        JSONType, default=None, nullable=True
    )


class CourseORM(Base):
    __tablename__ = "courses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="code")
    order: Mapped[int] = mapped_column(Integer, nullable=False)


class ModuleORM(Base):
    __tablename__ = "modules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    course: Mapped["CourseORM"] = relationship("CourseORM", backref="modules")


class LessonORM(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # theory/exercise
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    starter_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_cases: Mapped[Optional[Any]] = mapped_column(
        JSONType, default=list, nullable=True
    )
    question_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    course: Mapped["CourseORM"] = relationship("CourseORM", backref="lessons")
    module: Mapped["ModuleORM"] = relationship("ModuleORM", backref="lessons")


class CourseProgressORM(Base):
    __tablename__ = "course_progress"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    completed_lessons: Mapped[Any] = mapped_column(
        JSONType, default=list, nullable=False
    )
    last_accessed_lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_progress_user_course", "user_id", "course_id", unique=True),
    )
