"""Animation loop validation — every question must be visualizable.

Loop: Problem → Solution Repository / Groq → Animation Spec → Renderer → Interactive/Video
This gate ensures no question lands in the bank without a proven animation path.
"""

from typing import List

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationSeverity,
    ValidationUseCase,
)
from app.ports.code_executor import CodeExecutor
from app.services.solution_animation_service import SolutionAnimationService

from .base import BaseValidationUseCase


class AnimationValidationUseCase(BaseValidationUseCase):
    """Validates that the question can produce a cinematic animation for all 8 families."""

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.ANIMATION

    def __init__(self, executor: CodeExecutor | None = None):
        # Executor is optional in tests (allows structure-only validation when
        # Piston is unavailable); when absent we degrade to a WARNING not ERROR.
        self.executor = executor

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []

        if self.executor is None:
            issues.append(
                self._create_issue(
                    message="Animation validation skipped — no executor (Piston unavailable in this env)",
                    field="animation",
                    severity=ValidationSeverity.WARNING,
                )
            )
            return self._create_result(passed=True, issues=issues)

        # Required: examples[0].input must exist — animation input source.
        if not question.examples or not question.examples[0].input:
            issues.append(
                self._create_issue(
                    message="Animation requires examples[0].input — no input to trace",
                    field="examples[0].input",
                    severity=ValidationSeverity.ERROR,
                )
            )
            return self._create_result(passed=False, issues=issues)

        # Run the canonical animation loop: question → trace → planner → validator.
        try:
            service = SolutionAnimationService(executor=self.executor)
            animation = await service.build_animation(question.model_dump())
        except Exception as e:  # noqa: BLE001
            issues.append(
                self._create_issue(
                    message=f"Animation loop crashed: {type(e).__name__}: {e}",
                    field="animation",
                    severity=ValidationSeverity.ERROR,
                    details={"error": str(e)},
                )
            )
            return self._create_result(passed=False, issues=issues)

        if animation is None:
            issues.append(
                self._create_issue(
                    message=(
                        "Animation loop failed — no trace / no algorithm mapping / family not compilable. "
                        "Check reference_solutions.py mapping and examples[0].input"
                    ),
                    field="animation",
                    severity=ValidationSeverity.ERROR,
                    details={"question_id": question.id},
                )
            )
            return self._create_result(passed=False, issues=issues)

        # Success — beats were validated by AnimationValidator inside the service.
        steps = animation.get("steps", [])
        issues.append(
            self._create_issue(
                message=f"Animation loop passed — {len(steps)} cinematic beats (camera + badge)",
                field="animation",
                severity=ValidationSeverity.INFO,
                details={"steps": len(steps), "title": animation.get("title", "")},
            )
        )
        return self._create_result(passed=True, issues=issues)
