"""Seeded instructor logins (Issue #159, phase 2).

Professors and demonstrators must be able to log in against a real database,
so the seed script carries their accounts next to the admin seeds.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))


def test_instructor_seeds_cover_professor_and_ta():
    import seed_admin

    by_username = {u["username"]: u for u in seed_admin.INSTRUCTOR_SEED_USERS}
    assert by_username["professor.ada"]["role"] == "professor"
    assert by_username["demonstrator.turing"]["role"] == "ta"


def test_instructor_seeds_have_unique_login_identity():
    import seed_admin

    users = seed_admin.INSTRUCTOR_SEED_USERS
    assert len({u["username"] for u in users}) == len(users)
    assert len({u["email"] for u in users}) == len(users)
    for u in users:
        assert u["password"], f"seed {u['username']} needs a dev password"


def test_seed_admin_gate_allows_local_refuses_remote_without_confirm(monkeypatch):
    import seed_admin

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_x",
    )
    monkeypatch.delenv("SEED_LIVE_CONFIRM", raising=False)
    assert seed_admin._seed_allowed() is True
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example.com:5432/x")
    assert seed_admin._seed_allowed() is False
    monkeypatch.setenv("SEED_LIVE_CONFIRM", "YES-I-AM-SURE")
    assert seed_admin._seed_allowed() is True
