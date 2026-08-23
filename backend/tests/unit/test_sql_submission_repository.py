"""Unit tests for SqlSubmissionRepository — PostgreSQL-backed attempt history."""

import uuid
from datetime import datetime, timezone

import pytest_asyncio

from app.models.submission_schemas import SubmissionIn


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_submission_repository import SqlSubmissionRepository

    return SqlSubmissionRepository(test_db)


async def _make_user(test_db, uid=None):
    """Create a user row (FK target) and return its id."""
    from app.models.auth_schemas import UserInDB
    from app.repositories.sql_user_repository import SqlUserRepository

    uid = uid or str(uuid.uuid4())
    await SqlUserRepository(test_db).add(
        UserInDB(
            id=uid,
            username=f"subuser{uid[:8]}",
            email=f"sub{uid[:8]}@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
    )
    await test_db.commit()
    return uid


async def _make_question(test_db, qid):
    """Create a question row (FK target) and return its id."""
    from sqlalchemy import text

    await test_db.execute(
        text(
            "INSERT INTO questions "
            "(id, title, difficulty, category, company_tags, description, "
            " starter_code, examples, test_cases, constraints, hints, is_interactive) "
            "VALUES (:id, 'Test Q', 'easy', 'arrays', '[]', 'desc', '{}', '[]', "
            "'[]', '[]', '[]', 0)"
        ),
        {"id": qid},
    )
    await test_db.commit()
    return qid


@pytest_asyncio.fixture
async def user_id(test_db):
    return await _make_user(test_db)


@pytest_asyncio.fixture
async def question_id(test_db):
    return await _make_question(test_db, "q-submission-test")


class TestSqlSubmissionRepository:
    async def test_add_persists_attempt_with_zero_index(
        self, repo, test_db, user_id, question_id
    ):
        submission = await repo.add(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id,
                code="def solution():\n    pass",
                language="python",
                passed=False,
                error_signature="expected 4, got 3",
            ),
        )

        assert submission.passed is False
        assert submission.attempt_index == 0
        assert submission.error_signature == "expected 4, got 3"
        assert submission.user_id == user_id
        assert submission.question_id == question_id

    async def test_attempt_index_increments_per_question(
        self, repo, test_db, user_id, question_id
    ):
        await repo.add(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id, code="a", language="python", passed=False
            ),
        )
        second = await repo.add(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id, code="b", language="python", passed=True
            ),
        )
        other_question = await _make_question(test_db, "q-submission-other")
        other = await repo.add(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=other_question, code="c", language="python", passed=True
            ),
        )

        assert second.attempt_index == 1
        # A different question starts a fresh attempt sequence.
        assert other.attempt_index == 0

    async def test_list_by_user_newest_first(self, repo, test_db, user_id, question_id):
        await repo.add(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id, code="a", language="python", passed=False
            ),
        )
        await repo.add(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id, code="b", language="python", passed=True
            ),
        )

        items = await repo.list_by_user(user_id)

        assert len(items) == 2
        assert items[0].passed is True
        assert items[1].passed is False
        assert items[0].attempt_index == 1

    async def test_list_is_scoped_to_user(self, repo, test_db, user_id, question_id):
        await repo.add(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id, code="a", language="python", passed=True
            ),
        )
        other_user = await _make_user(test_db)
        await repo.add(
            user_id=other_user,
            submission=SubmissionIn(
                question_id=question_id, code="b", language="python", passed=False
            ),
        )

        items = await repo.list_by_user(user_id)
        assert len(items) == 1
        assert items[0].user_id == user_id
