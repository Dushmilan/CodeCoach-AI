from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class LessonType(str, Enum):
    THEORY = "theory"
    EXERCISE = "exercise"


class TestCase(BaseModel):
    input: str = Field(..., description="Test input")
    expected_output: str = Field(..., description="Expected output")
    description: Optional[str] = Field(None, description="Test case description")


class Lesson(BaseModel):
    id: str = Field(..., description="Unique lesson identifier")
    course_id: str = Field(..., description="Parent course ID")
    module_id: str = Field(..., description="Parent module ID")
    title: str = Field(..., description="Lesson title")
    type: LessonType = Field(..., description="Theory or exercise")
    content: str = Field(..., description="Markdown lesson body")
    order: int = Field(..., description="Display order within module")
    starter_code: Optional[str] = Field(None, description="Starter code for exercises")
    test_cases: Optional[List[TestCase]] = Field(None, description="Test assertions for exercises")
    language: str = Field(..., description="Language this lesson belongs to")


class Module(BaseModel):
    id: str = Field(..., description="Unique module identifier")
    course_id: str = Field(..., description="Parent course ID")
    title: str = Field(..., description="Module title")
    description: str = Field(..., description="Module overview")
    order: int = Field(..., description="Display order within course")
    lessons: List[str] = Field(..., description="Ordered list of lesson IDs")


class Course(BaseModel):
    id: str = Field(..., description="Unique course identifier")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course overview")
    language: str = Field(..., description="Programming language tag (python, c, java)")
    icon: str = Field(default="code", description="Icon identifier for the UI")
    order: int = Field(..., description="Display order")
    modules: List[str] = Field(..., description="Ordered list of module IDs")


class CourseSummary(BaseModel):
    id: str = Field(..., description="Course ID")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Short description")
    language: str = Field(..., description="Programming language")
    icon: str = Field(default="code")
    order: int = Field(..., description="Display order")
    progress: float = Field(default=0.0, description="User progress percentage 0-100")


class CourseProgress(BaseModel):
    user_id: str = Field(..., description="User ID")
    course_id: str = Field(..., description="Course ID")
    completed_lessons: List[str] = Field(default=[], description="Completed lesson IDs")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)
