import json
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any, Optional, Union, Literal
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
    ANIMATE = "animate"


CoachingSurface = Literal["questions", "learn"]


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
    content: str = Field(..., max_length=5000, description="Message content")


class CoachingRequest(BaseModel):
    problem: str = Field(
        ..., max_length=20000, description="The coding problem description"
    )
    code: str = Field(..., max_length=50000, description="User's current code attempt")
    language: Language = Field(..., description="Programming language")
    message: str = Field(..., max_length=5000, description="User's message or question")
    mode: CoachingMode = Field(default=CoachingMode.HINT, description="Coaching mode")
    difficulty: Difficulty = Field(
        default=Difficulty.MEDIUM, description="Problem difficulty"
    )
    lesson_context: Optional[str] = Field(
        None, max_length=2000, description="Lesson context for scoped coaching"
    )
    chat_history: Optional[List[ChatMessageContext]] = Field(
        default=[],
        max_length=20,
        description="Previous conversation messages for context",
    )
    initial_code: Optional[str] = Field(
        None,
        max_length=50000,
        description="Starter code the user began with, used to detect edits for animation",
    )
    surface: CoachingSurface = Field(
        default="questions",
        description=(
            "Client surface: 'questions' is the graph-aware interview tutor, "
            "'learn' is the graph-free curriculum companion."
        ),
    )

    @model_validator(mode="after")
    def require_lesson_context_for_learn(self):
        if self.surface == "learn" and not self.lesson_context:
            raise ValueError("lesson_context is required when surface is 'learn'")
        return self


class WarmRequest(BaseModel):
    """Fire-and-forget warm trigger for reusable coach learner context.

    question_id is logging-only (slug like "two-sum"); context stays
    user-scoped so anonymous callers never warm shared state.
    """

    question_id: Optional[str] = Field(
        default=None, max_length=128, description="Question slug being viewed"
    )


class WarmResponse(BaseModel):
    status: str = Field(..., description="warming | hit | disabled")
    warmed: bool = Field(..., description="True when a background warm was queued")
    ttl: int = Field(..., description="Coach context TTL seconds")


class SceneShape(BaseModel):
    """One declarative vector shape in an animation scene (data, never code).

    The AI supplies structured geometry only — the viewer instantiates Motion
    Canvas nodes from this data and animates them per the motion timeline.
    """

    id: str = Field(
        ..., max_length=64, description="Unique shape id referenced by motion ops"
    )
    type: Literal["rect", "ellipse", "line", "polygon", "text"] = Field(
        ..., description="Kind of vector primitive to draw"
    )
    x: float = Field(0, description="Center/left x position")
    y: float = Field(0, description="Center/top y position")
    width: Optional[float] = Field(None, gt=0, description="Width (rect/ellipse)")
    height: Optional[float] = Field(None, gt=0, description="Height (rect/ellipse)")
    radius: Optional[float] = Field(None, ge=0, description="Corner radius (rect)")
    points: Optional[List[List[float]]] = Field(
        None, description="Vertex list (line/polygon)"
    )
    text: Optional[str] = Field(None, max_length=200, description="Text content (text)")
    fontSize: Optional[float] = Field(None, gt=0, description="Font size (text)")
    fill: Optional[str] = Field(
        None, pattern=r"^#[0-9a-fA-F]{6}$", description="Hex fill color"
    )
    stroke: Optional[str] = Field(
        None, pattern=r"^#[0-9a-fA-F]{6}$", description="Hex stroke color"
    )
    lineWidth: Optional[float] = Field(None, gt=0, description="Stroke width")
    opacity: Optional[float] = Field(None, ge=0, le=1, description="Base opacity")


class MotionOp(BaseModel):
    """One tween applied to a shape in a step's timeline."""

    target: str = Field(..., max_length=64, description="Shape id this op animates")
    op: Literal[
        "appear",
        "disappear",
        "move",
        "fill",
        "stroke",
        "scale",
        "rotate",
        "label",
    ] = Field(..., description="What the op does to the shape")
    to: Optional[Any] = Field(
        None,
        description="Target: [x, y] for move, hex color for fill/stroke, number for scale/rotate",
    )
    duration: float = Field(0.3, gt=0, le=5, description="Tween duration in seconds")


class AnimationStep(BaseModel):
    """One frame of a declarative animation scene."""

    narration: str = Field(
        default="",
        max_length=300,
        description="Human-readable narration for this frame",
    )
    shapes: List[SceneShape] = Field(
        default_factory=list, description="Shapes created in this step"
    )
    motion: List[MotionOp] = Field(
        default_factory=list, description="Tweens applied to shapes this step"
    )


class AnimationScript(BaseModel):
    """Declarative, validated animation scene returned by the AI coach.

    A fully generic, data-driven scene: the model authors the subject and the
    algorithm visuals as primitives (shapes) plus a per-step motion timeline.
    No algorithm-type or subject-kind catalogs exist — every scene adapts to
    the question that produced it.
    """

    title: str = Field(
        default="", max_length=200, description="Short title shown above the animation"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional input data the scene references",
    )
    steps: List[AnimationStep] = Field(
        default_factory=list, description="Ordered frames of the animation"
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
    animation: Optional[AnimationScript] = Field(
        None, description="Declarative animation script to visualize the algorithm"
    )


class CoachingResponse(BaseModel):
    response: str = Field(..., description="AI coaching response (raw text)")
    structured: Optional[StructuredCoachingResponse] = Field(
        None, description="Structured AI coaching response"
    )
    mode: CoachingMode = Field(..., description="Coaching mode used")
    language: Language = Field(..., description="Programming language")


class QuestionInput(BaseModel):
    """Curated subset of a question sent to the animation generator.

    The full question context (description, examples, test cases, constraints)
    lets the model build scenes that reflect the actual problem — real values,
    real target, real-world subject — instead of guessing from a title.
    """

    title: Optional[str] = Field(None, max_length=500, description="Question title")
    description: Optional[str] = Field(
        None, max_length=20000, description="Full problem description"
    )
    category: Optional[str] = Field(
        None, max_length=100, description="Question category"
    )
    difficulty: Optional[str] = Field(
        None, max_length=20, description="Question difficulty"
    )
    id: Optional[str] = Field(
        None,
        max_length=100,
        description="Stable question id so the animation resolver pins the exact algorithm",
    )
    examples: List[Dict[str, Any]] = Field(
        default_factory=list, description="Example test cases"
    )
    test_cases: List[Dict[str, Any]] = Field(
        default_factory=list, description="Hidden test cases"
    )
    constraints: List[str] = Field(
        default_factory=list, description="Problem constraints"
    )
    starter: Optional[Dict[str, Any]] = Field(
        None, description="Starter code per language"
    )


class AnimateRequest(BaseModel):
    """Request for the standalone algorithm-animation endpoint.

    Unlike CoachingRequest this never carries chat history: the Animate
    viewer is independent of the AI Coach conversation, so nothing from the
    chat context is reused here.
    """

    problem: str = Field(
        ..., max_length=20000, description="The coding problem description"
    )
    code: str = Field(..., max_length=50000, description="User's current code attempt")
    language: Language = Field(..., description="Programming language")
    difficulty: Difficulty = Field(
        default=Difficulty.MEDIUM, description="Problem difficulty"
    )
    lesson_context: Optional[str] = Field(
        None, max_length=2000, description="Lesson context for scoped animation"
    )
    initial_code: Optional[str] = Field(
        None,
        max_length=50000,
        description="Starter code the user began with, used to detect edits for animation",
    )
    question: Optional[QuestionInput] = Field(
        None,
        description="Full question context so the scene reflects the actual problem",
    )


class AnimateResponse(BaseModel):
    """Visual algorithm animation for the standalone Animate viewer.

    This response intentionally has no chat text — it is played back as a
    Motion Canvas animation in a dedicated window, never as a chat message.
    """

    animation: AnimationScript = Field(
        ..., description="Validated visual algorithm animation"
    )


class CodeExecutionRequest(BaseModel):
    language: Language = Field(..., description="Programming language")
    code: str = Field(..., description="Source code to execute")
    stdin: str = Field(default="", description="Input to provide to the program")
    version: Optional[str] = Field(None, description="Specific language version")
    question_id: Optional[str] = Field(
        None,
        description=(
            "Question context for this run. When set and the execution exits "
            "non-zero, the crash is recorded in the attempt history and "
            "mistake-memory (best-effort)."
        ),
    )


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
