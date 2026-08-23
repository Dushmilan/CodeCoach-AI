from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

Base = declarative_base()

# Supabase/PostgreSQL is the only database — JSONB everywhere.
JSONType = JSONB()


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

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_plan", "plan"),
    )


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


class SubmissionORM(Base):
    """One persisted code attempt (submit) per user per question.

    This is the foundation of the mistake-memory data layer: per-user error
    history, spaced-repetition reviews, and attempt-journey replay all hang
    off this table.
    """

    __tablename__ = "submissions"
    id = Column(String(36), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        String(64),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(Text, nullable=False)
    language = Column(String(20), nullable=False)
    passed = Column(Boolean, nullable=False, default=False)
    error_signature = Column(String(255), nullable=True)
    attempt_index = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_submissions_user_question", "user_id", "question_id"),
        Index("ix_submissions_user_created", "user_id", "created_at"),
    )


class RescueQueueORM(Base):
    """Durable rescue re-surface queue (Ideas #4).

    One OPEN row (``status='abandoned'``) per (user, question), enforced by a
    partial unique index. Whether an open row is *due* is derived from
    ``due_at`` at read time - no scheduler job flips states.
    """

    __tablename__ = "rescue_queue"
    id = Column(String(36), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        String(64),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, server_default="abandoned")
    first_abandoned_at = Column(DateTime(timezone=True), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    resurface_count = Column(Integer, nullable=False, server_default="0")
    last_intervention_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "uq_rescue_queue_open_user_question",
            "user_id",
            "question_id",
            unique=True,
            postgresql_where=text("status = 'abandoned'"),
        ),
        Index("ix_rescue_queue_user_status_due", "user_id", "status", "due_at"),
    )


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
    request_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_daily_user_date", "user_id", "usage_date", unique=True),
    )


class RateLimitEventORM(Base):
    __tablename__ = "rate_limit_events"
    id = Column(String(36), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    ip = Column(String(45), nullable=False, index=True)
    reason = Column(String(50), nullable=False)
    endpoint = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_rate_limit_events_user_created", "user_id", "created_at"),
        Index("ix_rate_limit_events_ip_created", "ip", "created_at"),
    )


class SkillORM(Base):
    __tablename__ = "skills"
    slug = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False, default="")
    parent_id = Column(String(64), nullable=True)
    prerequisite_ids = Column(JSONType, default=list, nullable=False)


class QuestionSkillORM(Base):
    __tablename__ = "question_skills"
    id = Column(String(64), primary_key=True)
    question_id = Column(
        String(64),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_slug = Column(
        String(64),
        ForeignKey("skills.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight = Column(Float, nullable=False, default=1.0)

    __table_args__ = (
        Index("ix_question_skills_question", "question_id", "skill_slug"),
    )


class LearningEventORM(Base):
    __tablename__ = "learning_events"
    id = Column(String(64), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(40), nullable=False)
    question_id = Column(String(64), nullable=True)
    lesson_id = Column(String(36), nullable=True)
    skill_slug = Column(String(64), nullable=True, index=True)
    event_metadata = Column(JSONType, default=dict, nullable=False)
    occurred_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_learning_events_user_occurred", "user_id", "occurred_at"),
    )


class UserSkillStateORM(Base):
    __tablename__ = "user_skill_states"
    id = Column(String(64), primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_slug = Column(
        String(64),
        ForeignKey("skills.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mastery_score = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.0)
    evidence_count = Column(Integer, nullable=False, default=0)
    recent_error_count = Column(Integer, nullable=False, default=0)
    distinct_question_ids = Column(JSONType, default=list, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_user_skill_states_user_slug", "user_id", "skill_slug", unique=True),
    )
