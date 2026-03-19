from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"


class ExecuteRequest(BaseModel):
    code: str = Field(..., description="The code to execute")
    language: Language = Field(..., description="Programming language")
    stdin: Optional[str] = Field(None, description="Standard input for the program")
    args: List[str] = Field(default_factory=list, description="Command line arguments")
    compile_timeout: int = Field(default=10000, description="Compilation timeout in milliseconds")
    run_timeout: int = Field(default=5000, description="Execution timeout in milliseconds")
    memory_limit: int = Field(default=128000, description="Memory limit in KB")


class TestCase(BaseModel):
    input: str = Field(..., description="Input for the test case")
    expected: Any = Field(..., description="Expected output")
    description: Optional[str] = Field(None, description="Description of the test case")


class TestRequest(BaseModel):
    code: str = Field(..., description="The code to test")
    language: Language = Field(..., description="Programming language")
    test_cases: List[TestCase] = Field(..., description="List of test cases to run")
    function_name: Optional[str] = Field(None, description="Name of the function to test")
    setup_code: Optional[str] = Field(None, description="Setup code to run before tests")


class ExecutionResult(BaseModel):
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    exit_code: int = Field(..., description="Exit code")
    signal: Optional[str] = Field(None, description="Signal if process was killed")
    runtime: float = Field(..., description="Execution time in seconds")
    memory: int = Field(..., description="Memory used in KB")
    cpu_time: float = Field(..., description="CPU time used")


class TestResult(BaseModel):
    test_case: TestCase
    actual_output: Any = Field(..., description="Actual output from execution")
    passed: bool = Field(..., description="Whether the test passed")
    execution_result: ExecutionResult
    error_message: Optional[str] = Field(None, description="Error message if test failed")


class TestResponse(BaseModel):
    results: List[TestResult]
    total_tests: int = Field(..., description="Total number of tests")
    passed_tests: int = Field(..., description="Number of passed tests")
    failed_tests: int = Field(..., description="Number of failed tests")
    overall_success: bool = Field(..., description="Whether all tests passed")
    total_runtime: float = Field(..., description="Total execution time")