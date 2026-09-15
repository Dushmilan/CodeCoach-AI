from types import SimpleNamespace

from app.services.solution_animation_service import downsample_steps


def _s(action):
    return SimpleNamespace(action=action)


def test_downsample_keeps_first_last_and_key_actions_in_order():
    steps = [_s("compare")] + [_s("compare") for _ in range(200)] + [_s("found")]
    out = downsample_steps(steps, limit=96)
    assert len(out) <= 96
    assert out[0] is steps[0]
    assert out[-1] is steps[-1]
    assert any(s.action == "found" for s in out)
    pos = {id(s): k for k, s in enumerate(steps)}
    assert [pos[id(s)] for s in out] == sorted(pos[id(s)] for s in out)  # order kept
    actions = [s.action for s in out]
    assert actions[0] == "compare" and actions[-1] == "found"


def test_downsample_keeps_story_beats_when_key_events_overflow_limit():
    # Key actions alone exceed the limit: the old `key[:limit]` slice drops
    # both the intro beat and the final outro beat.
    steps = [_s("compare")] + [_s("swap") for _ in range(200)] + [_s("found")]
    out = downsample_steps(steps, limit=96)
    assert len(out) <= 96
    assert out[0] is steps[0]
    assert out[-1] is steps[-1]
    assert any(s.action == "found" for s in out)
