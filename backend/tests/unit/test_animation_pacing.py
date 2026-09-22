"""Unit tests for role-aware beat pacing (#240)."""

from app.services.animation_pacing import PacingProfile, apply_pacing


def _beat(role=None, duration=0.3):
    beat = {
        "narration": "x",
        "motion": [{"target": "a", "op": "move", "duration": duration}],
    }
    if role is not None:
        beat["role"] = role
    return beat


class TestApplyPacing:
    def test_rewrites_duration_by_role_and_strips_role(self):
        beats = apply_pacing([_beat(role="climax")])
        assert beats[0]["motion"][0]["duration"] == 0.5
        assert "role" not in beats[0]

    def test_beat_without_role_is_unchanged(self):
        beats = apply_pacing([_beat()])
        assert beats[0]["motion"][0]["duration"] == 0.3
        assert "role" not in beats[0]

    def test_duration_is_clamped_to_validator_window(self):
        loud = PacingProfile(intro=0.0, loop=0.4, climax=9.0, outro=0.3)
        beats = apply_pacing([_beat(role="intro"), _beat(role="climax")], loud)
        assert beats[0]["motion"][0]["duration"] == 0.1
        assert beats[1]["motion"][0]["duration"] == 5.0

    def test_tolerates_non_list_input(self):
        assert apply_pacing(None) is None
        assert apply_pacing([]) == []
