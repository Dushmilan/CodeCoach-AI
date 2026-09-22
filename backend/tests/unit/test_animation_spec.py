"""Unit tests for the semantic animation IR additions (#240)."""

import pytest
from pydantic import ValidationError

from app.models.animation_spec import AnimationStepSpec


class TestAnimationStepSpecFields:
    def test_new_fields_default_to_none(self):
        step = AnimationStepSpec(action="compare")
        assert step.line is None
        assert step.annotation is None
        assert step.role is None

    def test_accepts_line_annotation_and_role(self):
        step = AnimationStepSpec(
            action="found", index=3, line=42, annotation="target found", role="climax"
        )
        assert step.line == 42
        assert step.annotation == "target found"
        assert step.role == "climax"

    def test_rejects_non_positive_line(self):
        with pytest.raises(ValidationError):
            AnimationStepSpec(action="compare", line=0)

    def test_rejects_unknown_role(self):
        with pytest.raises(ValidationError):
            AnimationStepSpec(action="compare", role="middle")
