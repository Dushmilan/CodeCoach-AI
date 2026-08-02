import json
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum


def _json_to_str(v: Any, compact: bool = False) -> str:
    if isinstance(v, dict):
        return json.dumps(v, separators=(",", ":") if compact else None)
    if isinstance(v, (list, int, float)):
        return json.dumps(v, separators=(",", ":") if compact else None)
    if isinstance(v, bool):
        return str(v).lower()
    if v is None:
        return ""
    return v


class CoachingMode(str, Enum):
    HINT = "hint"
    REVIEW = "review"
    EXPLAIN = "explain"
    DEBUG = "debug"
    FREEFORM = "freeform"


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    TYPESCRIPT = "typescript"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ChatMessageContext(BaseModel):
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")


class CoachingRequest(BaseModel):
    problem: str = Field(..., description="The coding problem description")
    code: str = Field(..., description="User's current code attempt")
    language: Language = Field(..., description="Programming language")
    message: str = Field(..., description="User's message or question")
    mode: CoachingMode = Field(default=CoachingMode.HINT, description="Coaching mode")
    difficulty: Difficulty = Field(
        default=Difficulty.MEDIUM, description="Problem difficulty"
    )
    lesson_context: Optional[str] = Field(
        None, description="Lesson context for scoped coaching"
    )
    chat_history: Optional[List[ChatMessageContext]] = Field(
        default=[], description="Previous conversation messages for context"
    )


class StructuredCoachingResponse(BaseModel):
    """Structured AI coaching response with categorized sections."""

    summary: str = Field(..., description="Brief summary of the response")
    hints: list[str] = Field(
        default=[], description="List of hints for solving the problem"
    )
    code_review: Optional[str] = Field(None, description="Code review feedback")
    complexity_analysis: Optional[str] = Field(
        None, description="Time and space complexity analysis"
    )
    suggestions: list[str] = Field(
        default=[], description="List of improvement suggestions"
    )
    edge_cases: list[str] = Field(
        default=[], description="List of edge cases to consider"
    )
    explanation: Optional[str] = Field(
        None, description="Detailed explanation of concepts"
    )
    debug_help: Optional[str] = Field(None, description="Debugging assistance")


class CoachingResponse(BaseModel):
    response: str = Field(..., description="AI coaching response (raw text)")
    structured: Optional[StructuredCoachingResponse] = Field(
        None, description="Structured AI coaching response"
    )
    mode: CoachingMode = Field(..., description="Coaching mode used")
    language: Language = Field(..., description="Programming language")


class CodeExecutionRequest(BaseModel):
    language: Language = Field(..., description="Programming language")
    code: str = Field(..., description="Source code to execute")
    stdin: str = Field(default="", description="Input to provide to the program")
    version: Optional[str] = Field(None, description="Specific language version")


class CodeExecutionResult(BaseModel):
    stdout: str = Field(..., description="Standard output from execution")
    stderr: str = Field(..., description="Standard error from execution")
    exit_code: int = Field(..., description="Exit code from execution")
    execution_time: Optional[float] = Field(
        None, description="Execution time in seconds (float from Piston wall_time)"
    )
    memory_usage: Optional[int] = Field(None, description="Memory usage in bytes")
    language: str = Field(..., description="Language used")
    version: str = Field(..., description="Language version")


class TestCase(BaseModel):
    input: Union[str, Dict[str, Any]] = Field(..., description="Test input")
    expected_output: Union[str, Dict[str, Any]] = Field(
        ..., description="Expected output"
    )
    description: Optional[str] = Field(None, description="Test case description")
    hidden: bool = Field(
        default=False, description="Whether this is a hidden test case"
    )

    @field_validator("input", "expected_output", mode="before")
    @classmethod
    def normalize_to_string(cls, v):
        return _json_to_str(v, compact=True)


class CodeValidationRequest(BaseModel):
    """Request for code validation against test cases."""

    language: Language = Field(..., description="Programming language")
    code: str = Field(..., description="Source code to validate")
    test_cases: List[TestCase] = Field(
        ..., description="List of test cases to validate against"
    )


class ValidationResult(BaseModel):
    """Result of code validation."""

    total_tests: int = Field(..., description="Total number of test cases")
    passed_tests: int = Field(..., description="Number of test cases that passed")
    success_rate: float = Field(..., description="Success rate as a percentage")
    results: List[Dict[str, Any]] = Field(
        ..., description="Detailed results for each test case"
    )
    formatted_output: str = Field(..., description="User-friendly formatted output")


class Example(BaseModel):
    input: Union[str, Dict[str, Any]] = Field(..., description="Example input")
    output: Union[str, Dict[str, Any]] = Field(default="", description="Example output")
    explanation: Optional[str] = Field(None, description="Explanation of the example")

    @field_validator("input", "output", mode="before")
    @classmethod
    def normalize_field_to_string(cls, v):
        return _json_to_str(v)

    @model_validator(mode="before")
    @classmethod
    def normalize_example(cls, data):
        if isinstance(data, dict):
            if "expected_output" in data and "output" not in data:
                data["output"] = data.pop("expected_output")
        return data


class StarterCode(BaseModel):
    python: str = Field(default="", description="Python starter code")
    javascript: str = Field(default="", description="JavaScript starter code")
    java: str = Field(default="", description="Java starter code")


class Question(BaseModel):
    id: str = Field(..., description="Unique question identifier")
    title: str = Field(..., description="Question title")
    difficulty: Difficulty = Field(..., description="Question difficulty")
    category: str = Field(..., description="Question category")
    company_tags: List[str] = Field(
        default=[], description="Companies that ask this question"
    )
    description: Union[str, Dict[str, Any], List] = Field(
        ..., description="Detailed problem description"
    )
    starter: Union[StarterCode, str, List, Dict[str, Any]] = Field(
        ..., description="Starter code for each language"
    )
    examples: List[Example] = Field(..., description="Example test cases")
    test_cases: List[TestCase] = Field(..., description="Test cases for validation")
    hints: List[str] = Field(default=[], description="Hints for solving the problem")
    solution: Optional[Union[str, Dict[str, Any]]] = Field(
        None, description="Optimal solution explanation"
    )
    time_complexity: Optional[str] = Field(
        None, description="Time complexity of optimal solution"
    )
    space_complexity: Optional[str] = Field(
        None, description="Space complexity of optimal solution"
    )
    constraints: List[str] = Field(default=[], description="Problem constraints")
    is_interactive: bool = Field(
        default=False, description="Whether this is an interactive terminal challenge"
    )

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, v):
        if isinstance(v, dict):
            parts = []
            for key in sorted(v.keys()):
                val = v[key]
                if isinstance(val, str):
                    parts.append(val)
            return "\n\n".join(parts) if parts else json.dumps(v)
        if isinstance(v, list):
            return "\n\n".join(str(x) for x in v)
        return v

    @field_validator("solution", mode="before")
    @classmethod
    def normalize_solution(cls, v):
        return _json_to_str(v)

    @model_validator(mode="before")
    @classmethod
    def normalize_starter(cls, data):
        if not isinstance(data, dict):
            return data
        starter = data.get("starter")
        if starter is None:
            return data
        if isinstance(starter, str):
            lang = starter.lower()
            if lang in (
                "python",
                "javascript",
                "java",
                "typescript",
                "c",
                "cpp",
                "go",
                "rust",
            ):
                data["starter"] = {"python": "", "javascript": "", "java": ""}
        elif isinstance(starter, list):
            mapped = {}
            for entry in starter:
                if isinstance(entry, dict):
                    lang = entry.get("language", "")
                    code = entry.get("code", "")
                    if lang:
                        mapped[lang] = code
            for lang in ("python", "javascript", "java"):
                mapped.setdefault(lang, "")
            data["starter"] = mapped
        elif isinstance(starter, dict):
            for lang in ("python", "javascript", "java"):
                starter.setdefault(lang, "")
        return data


class QuestionSummary(BaseModel):
    id: str = Field(..., description="Question ID")
    title: str = Field(..., description="Question title")
    difficulty: Difficulty = Field(..., description="Question difficulty")
    category: str = Field(..., description="Question category")
    company_tags: List[str] = Field(default=[], description="Company tags")
    solved: bool = Field(default=False, description="Whether user has solved this")


class QuestionsListResponse(BaseModel):
    questions: List[QuestionSummary] = Field(..., description="List of questions")
    total: int = Field(..., description="Total number of questions")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=20, description="Questions per page")


class SubmitRequest(BaseModel):
    question_id: str = Field(..., description="Question ID to submit against")
    language: Language = Field(..., description="Programming language")
    code: str = Field(..., description="Source code to submit")


class SubmitResult(BaseModel):
    index: int = Field(..., description="Test case index (1-based)")
    passed: bool = Field(..., description="Whether the test case passed")
    input: str = Field(default="", description="Test input (empty for hidden)")
    expected: str = Field(default="", description="Expected output (empty for hidden)")
    actual: str = Field(default="", description="Actual output (empty for hidden)")
    hidden: bool = Field(
        default=False, description="Whether this is a hidden test case"
    )


class SubmitResponse(BaseModel):
    passed: bool = Field(..., description="Whether all test cases passed")
    total: int = Field(..., description="Total number of test cases")
    passed_count: int = Field(..., description="Number of test cases passed")
    results: List[SubmitResult] = Field(
        ..., description="Detailed results per test case"
    )


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: str = Field(..., description="Current timestamp")
    dependencies: Dict[str, str] = Field(
        default={}, description="Dependency health status"
    )
