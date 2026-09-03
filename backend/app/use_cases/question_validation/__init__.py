"""Question validation use cases.

Each validation strategy lives in its own module under this package.
The facade service (QuestionValidatorService) lives in
app.services.question_validator and orchestrates these use cases.
"""

from .base import BaseValidationUseCase
from .structure import StructureValidationUseCase
from .test_cases import TestCaseValidationUseCase
from .starter_code import StarterCodeValidationUseCase
from .solution import SolutionValidationUseCase
from .time_limits import TimeLimitValidationUseCase
from .function_signature import FunctionSignatureValidationUseCase
from .output_format import OutputFormatValidationUseCase
from .animation import AnimationValidationUseCase

__all__ = [
    "BaseValidationUseCase",
    "StructureValidationUseCase",
    "TestCaseValidationUseCase",
    "StarterCodeValidationUseCase",
    "SolutionValidationUseCase",
    "TimeLimitValidationUseCase",
    "FunctionSignatureValidationUseCase",
    "OutputFormatValidationUseCase",
    "AnimationValidationUseCase",
]
