from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"


class TestCase(BaseModel):
    input: List[Any]
    expected: Any
    function_name: str
    python_function_name: str
    java_function_name: str
    in_place: bool = False


class Example(BaseModel):
    input: str
    output: str


class Question(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    category: str
    description: str
    starter: Dict[str, str]
    test_cases: List[TestCase] = Field(alias="testCases")
    examples: List[Example]
    hints: List[str]
    solution: str
    time_complexity: str = Field(alias="timeComplexity")
    space_complexity: str = Field(alias="spaceComplexity")

    class Config:
        populate_by_name = True


class QuestionList(BaseModel):
    questions: List[Question]