from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

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

class CoachingRequest(BaseModel):
    problem: str = Field(..., description="The coding problem description")
    code: str = Field(..., description="User's current code attempt")
    language: Language = Field(..., description="Programming language")
    message: str = Field(..., description="User's message or question")
    mode: CoachingMode = Field(default=CoachingMode.HINT, description="Coaching mode")
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM, description="Problem difficulty")

class StructuredCoachingResponse(BaseModel):
    """Structured AI coaching response with categorized sections."""
    summary: str = Field(..., description="Brief summary of the response")
    hints: list[str] = Field(default=[], description="List of hints for solving the problem")
    code_review: Optional[str] = Field(None, description="Code review feedback")
    complexity_analysis: Optional[str] = Field(None, description="Time and space complexity analysis")
    suggestions: list[str] = Field(default=[], description="List of improvement suggestions")
    edge_cases: list[str] = Field(default=[], description="List of edge cases to consider")
    explanation: Optional[str] = Field(None, description="Detailed explanation of concepts")
    debug_help: Optional[str] = Field(None, description="Debugging assistance")


class CoachingResponse(BaseModel):
    response: str = Field(..., description="AI coaching response (raw text)")
    structured: Optional[StructuredCoachingResponse] = Field(None, description="Structured AI coaching response")
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
    execution_time: Optional[int] = Field(None, description="Execution time in milliseconds")
    memory_usage: Optional[int] = Field(None, description="Memory usage in bytes")
    language: str = Field(..., description="Language used")
    version: str = Field(..., description="Language version")

class TestCase(BaseModel):
    input: str = Field(..., description="Test input")
    expected_output: str = Field(..., description="Expected output")
    description: Optional[str] = Field(None, description="Test case description")
    hidden: bool = Field(default=False, description="Whether this is a hidden test case")


class CodeValidationRequest(BaseModel):
    """Request for code validation against test cases."""
    language: Language = Field(..., description="Programming language")
    code: str = Field(..., description="Source code to validate")
    test_cases: List[TestCase] = Field(..., description="List of test cases to validate against")


class ValidationResult(BaseModel):
    """Result of code validation."""
    total_tests: int = Field(..., description="Total number of test cases")
    passed_tests: int = Field(..., description="Number of test cases that passed")
    success_rate: float = Field(..., description="Success rate as a percentage")
    results: List[Dict[str, Any]] = Field(..., description="Detailed results for each test case")
    formatted_output: str = Field(..., description="User-friendly formatted output")

class Example(BaseModel):
    input: str = Field(..., description="Example input")
    output: str = Field(..., description="Example output")
    explanation: Optional[str] = Field(None, description="Explanation of the example")

class StarterCode(BaseModel):
    python: str = Field(..., description="Python starter code")
    javascript: str = Field(..., description="JavaScript starter code")
    java: str = Field(..., description="Java starter code")

class Question(BaseModel):
    id: str = Field(..., description="Unique question identifier")
    title: str = Field(..., description="Question title")
    difficulty: Difficulty = Field(..., description="Question difficulty")
    category: str = Field(..., description="Question category")
    company_tags: List[str] = Field(default=[], description="Companies that ask this question")
    description: str = Field(..., description="Detailed problem description")
    starter: StarterCode = Field(..., description="Starter code for each language")
    examples: List[Example] = Field(..., description="Example test cases")
    test_cases: List[TestCase] = Field(..., description="Test cases for validation")
    hints: List[str] = Field(default=[], description="Hints for solving the problem")
    solution: Optional[str] = Field(None, description="Optimal solution explanation")
    time_complexity: Optional[str] = Field(None, description="Time complexity of optimal solution")
    space_complexity: Optional[str] = Field(None, description="Space complexity of optimal solution")
    constraints: List[str] = Field(default=[], description="Problem constraints")

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

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: str = Field(..., description="Current timestamp")
    dependencies: Dict[str, str] = Field(default={}, description="Dependency health status")