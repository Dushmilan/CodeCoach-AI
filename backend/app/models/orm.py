from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    Date,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

Base = declarative_base()

# Use JSONB for PostgreSQL, JSON for MySQL
JSONType = JSONB().with_variant(JSON, "mysql")


class UserORM(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    is_active = Column(Integer, default=1, nullable=False)
    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)
    role = Column(String(20), server_default="user", nullable=False)
    plan = Column(String(20), server_default="free", nullable=False)

    __table_args__ = (Index("ix_users_role", "role"),)


class QuestionORM(Base):
    __tablename__ = "questions"
    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    difficulty = Column(String(10), nullable=False)  # easy/medium/hard
    category = Column(String(100), nullable=False, index=True)
    company_tags = Column(JSONType, default=list, nullable=False)
    description = Column(Text, nullable=False)
    starter_code = Column(
        JSONType, default=dict, nullable=False
    )  # {"python": "...", "javascript": "..."}
    examples = Column(JSONType, default=list, nullable=False)
    test_cases = Column(JSONType, default=list, nullable=False)
    hints = Column(JSONType, default=list, nullable=False)
    solution = Column(Text, nullable=True)
    time_complexity = Column(String(200), nullable=True)
    space_complexity = Column(String(200), nullable=True)
    constraints = Column(JSONType, default=list, nullable=False)
    is_interactive = Column(Integer, default=0, nullable=False)
    validation_status = Column(JSONType, default=None, nullable=True)

    __table_args__ = (
        Index(
            "ix_questions_company_tags",
            "company_tags",
            postgresql_using="gin",
        ),
    )


class CourseORM(Base):
    __tablename__ = "courses"
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    icon = Column(String(50), default="code")
    order = Column(Integer, nullable=False)


class ModuleORM(Base):
    __tablename__ = "modules"
    id = Column(String(36), primary_key=True)
    course_id = Column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    course = relationship("CourseORM", backref="modules")


class LessonORM(Base):
    __tablename__ = "lessons"
    id = Column(String(36), primary_key=True)
    course_id = Column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_id = Column(
        String(36),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # theory/exercise
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    starter_code = Column(Text, nullable=True)
    test_cases = Column(JSONType, default=list, nullable=True)
    question_id = Column(
        String(64),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    language = Column(String(50), nullable=False)
    course = relationship("CourseORM", backref="lessons")
    module = relationship("ModuleORM", backref="lessons")


class CourseProgressORM(Base):
    __tablename__ = "course_progress"
    id = Column(String(64), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = Column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    completed_lessons = Column(JSONType, default=list, nullable=False)
    last_accessed_lesson_id = Column(String(36), nullable=True)
    started_at = Column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    last_accessed_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_progress_user_course", "user_id", "course_id", unique=True),
    )


class UserUsageEventORM(Base):
    __tablename__ = "user_usage_events"
    id = Column(String(36), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = Column(String(20), nullable=False, default="groq")
    model = Column(String(100), nullable=False)
    endpoint = Column(String(50), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (Index("ix_usage_events_user_created", "user_id", "created_at"),)


class UserDailyUsageORM(Base):
    __tablename__ = "user_daily_usage"
    id = Column(String(36), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usage_date = Column(Date, nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_daily_user_date", "user_id", "usage_date", unique=True),
    )
