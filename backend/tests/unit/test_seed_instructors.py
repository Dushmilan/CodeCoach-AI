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
