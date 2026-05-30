import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

# ...

        validated_at=datetime.now(timezone.utc),
    )


class TestQuestionValidationValidate:
    def test_validate_full_success(self, test_client: TestClient):
        mock_validator = MagicMock()
        mock_validator.validate_question = AsyncMock(
            return_value=make_mock_result(valid=True)
        )

        from app.api.question_validation import get_validator_service
        app.dependency_overrides[get_validator_service] = lambda: mock_validator
        try:
            response = test_client.post(
                "/api/question-validation/validate",
                json=VALID_QUESTION,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["question_id"] == "test-question"
        finally:
            app.dependency_overrides.clear()

    def test_validate_full_failure(self, test_client: TestClient):
        mock_validator = MagicMock()
        result = make_mock_result(valid=False)
        result.results[ValidationUseCase.STRUCTURE] = UseCaseValidationResult(
            use_case=ValidationUseCase.STRUCTURE,
            passed=False,
            issues=[
                ValidationIssue(
                    use_case=ValidationUseCase.STRUCTURE,
                    severity=ValidationSeverity.ERROR,
                    message="Missing required field",
                    field="test_field",
                )
            ],
        )
        result.error_count = 1
        result.total_issues = 1
        mock_validator.validate_question = AsyncMock(return_value=result)

        from app.api.question_validation import get_validator_service
        app.dependency_overrides[get_validator_service] = lambda: mock_validator
        try:
            response = test_client.post(
                "/api/question-validation/validate",
                json=VALID_QUESTION,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert data["error_count"] == 1
        finally:
            app.dependency_overrides.clear()

    def test_validate_invalid_input(self, test_client: TestClient):
        response = test_client.post(
            "/api/question-validation/validate",
            json={"id": "no-fields"},
        )
        assert response.status_code == 422


class TestQuestionValidationQuick:
    def test_quick_validate_success(self, test_client: TestClient):
        mock_validator = MagicMock()
        mock_validator.quick_validate = AsyncMock(
            return_value=make_mock_result(valid=True)
        )

        from app.api.question_validation import get_validator_service
        app.dependency_overrides[get_validator_service] = lambda: mock_validator
        try:
            response = test_client.post(
                "/api/question-validation/validate/quick",
                json=VALID_QUESTION,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
        finally:
            app.dependency_overrides.clear()


class TestQuestionValidationUseCases:
    def test_validate_with_specific_use_cases(self, test_client: TestClient):
        mock_validator = MagicMock()
        mock_validator.validate_question = AsyncMock(
            return_value=make_mock_result(valid=True)
        )

        from app.api.question_validation import get_validator_service
        app.dependency_overrides[get_validator_service] = lambda: mock_validator
        try:
            response = test_client.post(
                "/api/question-validation/validate/use-cases",
                json={"question": VALID_QUESTION, "use_cases": ["structure", "output_format"]},
            )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_validate_with_invalid_use_case_name(self, test_client: TestClient):
        mock_validator = MagicMock()

        from app.api.question_validation import get_validator_service
        app.dependency_overrides[get_validator_service] = lambda: mock_validator
        try:
            response = test_client.post(
                "/api/question-validation/validate/use-cases",
                json={"question": VALID_QUESTION, "use_cases": ["nonexistent_use_case"]},
            )
            assert response.status_code == 400
            assert "Invalid use case" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestQuestionValidationBatch:
    def test_batch_validate(self, test_client: TestClient):
        mock_validator = MagicMock()
        mock_validator.validate_batch = AsyncMock(
            return_value=[make_mock_result(valid=True), make_mock_result(valid=False)]
        )

        from app.api.question_validation import get_validator_service
        app.dependency_overrides[get_validator_service] = lambda: mock_validator
        try:
            response = test_client.post(
                "/api/question-validation/batch-validate",
                json=[VALID_QUESTION, VALID_QUESTION],
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["valid_count"] == 1
            assert data["invalid_count"] == 1
        finally:
            app.dependency_overrides.clear()


class TestQuestionValidationInfo:
    def test_get_use_cases(self, test_client: TestClient):
        response = test_client.get("/api/question-validation/use-cases")
        assert response.status_code == 200
        data = response.json()
        assert "use_cases" in data
        use_case_names = [uc["name"] for uc in data["use_cases"]]
        assert "structure" in use_case_names
        assert "test_cases" in use_case_names
        assert "starter_code" in use_case_names
        assert "solution" in use_case_names
        assert "time_limits" in use_case_names
        assert "function_signature" in use_case_names
        assert "output_format" in use_case_names

    def test_get_config(self, test_client: TestClient):
        response = test_client.get("/api/question-validation/config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "test_cases" in data["config"]
        assert "time_limits" in data["config"]
        assert "function_signature" in data["config"]
        assert "output_format" in data["config"]


class TestQuestionValidationSummary:
    def test_get_summary(self, test_client: TestClient):
        mock_validator = MagicMock()
        mock_validator.get_validation_summary = MagicMock(
            return_value={
                "question_id": "test-q",
                "valid": True,
                "total_issues": 0,
                "use_cases_run": 1,
                "use_cases_passed": 1,
            }
        )

        from app.api.question_validation import get_validator_service
        app.dependency_overrides[get_validator_service] = lambda: mock_validator
        try:
            response = test_client.post(
                "/api/question-validation/summary",
                json={
                    "question_id": "test-q",
                    "valid": True,
                    "results": {},
                    "total_issues": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "validated_at": "2025-01-01T00:00:00Z",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
        finally:
            app.dependency_overrides.clear()
