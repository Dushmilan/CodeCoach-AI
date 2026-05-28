# Architecture Improvement Plan

This document outlines architectural refactoring opportunities for the CodeCoach AI codebase, focused on deepening modules, improving testability, and increasing AI-navigability.

---

## 1. Deepen the CodeExecutor Port

*   **Files**: `backend/app/api/submit.py`, `backend/app/services/piston_service.py`, `frontend/src/features/code-execution/code-execution.service.ts`
*   **Problem**: Currently, the `CodeExecutor` **Module** is a shallow pass-through to the Piston API. Orchestration logic (test suite looping, assertion, hidden case redaction) leaks across the **Seam** into `submit.py`, and is duplicated in the frontend. This shallow **Interface** forces inefficient sequential network requests ($N$ requests for $N$ test cases).
*   **Solution**: Deepen the `CodeExecutor` **Interface** by introducing a `TestSuite` abstraction and an `evaluate_suite(language, code, test_cases)` method.
*   **Benefits**:
    *   **Locality**: Logic concentrates in the adapter, removing leakage from controllers.
    *   **Leverage**: Single-request execution for entire test suites drastically reduces latency and complexity for callers.
*   **Recommendation Strength**: `Strong`

## 2. Unify Domain Models (Question vs Lesson)

*   **Files**: `backend/app/models/course_schemas.py`, `backend/app/models/schemas.py`
*   **Problem**: `Question` and `Lesson` **Modules** maintain parallel (and drifting) models for coding exercises, duplicating `TestCase` definitions. `Question` has evolved robust validation, while `Lesson` remains naive, creating significant technical debt.
*   **Solution**: Make `Lesson` reference a `Question` by ID. Delegate all exercise validation, parsing, and execution rules to the `Question` **Module**.
*   **Benefits**:
    *   **Locality**: Single source of truth for validation rules.
    *   **Leverage**: Curriculum system inherits all robustness from the Question domain.
*   **Recommendation Strength**: `Strong`

## 3. Dissolve the QuestionValidator God Module

*   **Files**: `backend/app/services/question_validator.py`
*   **Problem**: `question_validator.py` is a 53KB god **Module** that packs all validation rules (signatures, structure, time limits) into a single file. This shallow **Implementation** (in terms of file structure) hinders maintainability.
*   **Solution**: Introduce a physical **Seam**. Split the file into a `use_cases/question_validation/` directory with discrete **Adapters** per validation rule, wrapped behind a `QuestionValidator` facade.
*   **Benefits**:
    *   **Locality**: Maintainers can modify specific rules without wading through 50KB of code.
    *   **Leverage**: Facade pattern preserves a deep **Interface** for callers while allowing highly granular implementation.
*   **Recommendation Strength**: `Worth exploring`
