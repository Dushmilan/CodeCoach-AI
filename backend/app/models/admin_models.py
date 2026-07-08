from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserAdminUpdate(BaseModel):
    role: Optional[str] = Field(
        None, description="User role (user, admin, super_admin)"
    )
    is_active: Optional[bool] = Field(None, description="User account active status")
    oauth_provider: Optional[str] = Field(None, description="OAuth provider")


class UserDetailResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool
    role: str
    oauth_provider: Optional[str]
    oauth_id: Optional[str]


class StatsResponse(BaseModel):
    users: Dict[str, Any]
    questions: Dict[str, Any]
    courses: Dict[str, Any]
    system: Dict[str, Any]
    generation: Dict[str, Any]


class QuestionFilter(BaseModel):
    difficulty: Optional[str] = None
    category: Optional[str] = None
    has_solution: Optional[bool] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class QuestionImportResult(BaseModel):
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]


class CourseProgressDetail(BaseModel):
    course_id: str
    completed_lessons: List[str]
    last_accessed_lesson_id: Optional[str]
    progress: float


# ── Curriculum CRUD Schemas ──────────────────────────────


class CourseCreate(BaseModel):
    id: str = Field(..., description="Unique slug (e.g. python-fundamentals)")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course overview")
    language: str = Field(..., description="Programming language tag (python, c, java)")
    icon: str = Field(default="code", description="Icon identifier for UI")
    order: int = Field(..., description="Display order")


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    icon: Optional[str] = None
    order: Optional[int] = None


class ModuleCreate(BaseModel):
    id: str = Field(..., description="Unique slug")
    course_id: str = Field(..., description="Parent course ID")
    title: str = Field(..., description="Module title")
    description: str = Field(..., description="Module overview")
    order: int = Field(..., description="Display order within course")


class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class LessonCreate(BaseModel):
    id: str = Field(..., description="Unique slug")
    course_id: str = Field(..., description="Parent course ID")
    module_id: str = Field(..., description="Parent module ID")
    title: str = Field(..., description="Lesson title")
    type: str = Field(..., description="theory or exercise")
    content: str = Field(..., description="Markdown lesson body")
    order: int = Field(..., description="Display order within module")
    starter_code: Optional[str] = Field(None, description="Starter code for exercises")
    test_cases: Optional[List[Dict[str, Any]]] = Field(
        None, description="Test cases for exercises"
    )
    question_id: Optional[str] = Field(
        None, description="Linked question ID for exercises"
    )
    language: str = Field(..., description="Programming language")


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None
    starter_code: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    question_id: Optional[str] = None
    language: Optional[str] = None


class QuestionCreate(BaseModel):
    id: str = Field(..., description="Unique question identifier")
    title: str = Field(..., description="Question title")
    difficulty: str = Field(..., description="easy, medium, or hard")
    category: str = Field(..., description="Question category (e.g. arrays, strings)")
    description: str = Field(..., description="Problem description")
    company_tags: List[str] = Field(default=[], description="Company tags")
    starter_code: Optional[Dict[str, str]] = Field(
        None, description="Starter code per language"
    )
    examples: Optional[List[Dict[str, Any]]] = Field(
        None, description="Example test cases"
    )
    test_cases: Optional[List[Dict[str, Any]]] = Field(
        None, description="Test cases for validation"
    )
    hints: List[str] = Field(default=[], description="Hints for solving")
    solution: Optional[str] = Field(None, description="Solution explanation")
    time_complexity: Optional[str] = Field(None, description="Time complexity")
    space_complexity: Optional[str] = Field(None, description="Space complexity")
    constraints: List[str] = Field(default=[], description="Problem constraints")


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    company_tags: Optional[List[str]] = None
    starter_code: Optional[Dict[str, str]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    hints: Optional[List[str]] = None
    solution: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    constraints: Optional[List[str]] = None
