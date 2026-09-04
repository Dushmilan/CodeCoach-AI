"""RED: adapter state persistence — sent/submitted/failed must be durable.

Covers the system-design contract from
Docs/plans/2026-09-03-adapter-state-persistence.md:
- every coaching intent persists sent -> completed/failed
- every execution intent persists sent -> executed/failed
- every submit persists sent before grading, then graded/failed
"""

import uuid
from datetime import datetime, timezone

import pytest_asyncio


@pytest_asyncio.fixture
async def _ids(test_db):
    from app.models.auth_schemas import UserInDB
    from app.repositories.sql_user_repository import SqlUserRepository
    from sqlalchemy import text

    uid = str(uuid.uuid4())
    await SqlUserRepository(test_db).add(
        UserInDB(
            id=uid,
            username=f"adapter{uid[:8]}",
            email=f"adapter{uid[:8]}@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
    )
    await test_db.commit()
    qid = f"q-adapter-{uid[:8]}"
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
    return uid, qid


class TestAdapterStatePersistence:
    async def test_submission_supports_sent_status(self, test_db, _ids):
        from app.repositories.sql_submission_repository import (
            SqlSubmissionRepository,
        )
        from app.models.submission_schemas import SubmissionIn

        user_id, question_id = _ids
        repo = SqlSubmissionRepository(test_db)
        sent = await repo.create_sent(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id,
                code="print('hi')",
                language="python",
                passed=False,
            ),
        )
        assert sent.status == "sent"

        graded = await repo.mark_graded(sent.id, passed=True, error_signature=None)
        assert graded.status == "graded"
        assert graded.passed is True

    async def test_submit_persists_failed_when_executor_raises(self, test_db, _ids):
        from app.services.submit_grading_service import grade_submission_with_state

        user_id, question_id = _ids

        class _Boom:
            async def evaluate_suite(self, language, code, test_cases):
                raise RuntimeError("piston down")

        result = await grade_submission_with_state(
            db=test_db,
            executor=_Boom(),
            user_id=user_id,
            question_id=question_id,
            code="print('hi')",
            language="python",
        )
        assert result.status == "failed"

    async def test_coaching_interaction_sent_to_completed(self, test_db, _ids):
        from app.repositories.sql_coaching_interaction_repository import (
            SqlCoachingInteractionRepository,
        )

        user_id, question_id = _ids
        repo = SqlCoachingInteractionRepository(test_db)
        interaction = await repo.create_sent(
            user_id=user_id,
            question_id=question_id,
            mode="hint",
            language="python",
            problem_hash="ph",
            code_hash="ch",
            idempotency_key=f"idem-{uuid.uuid4().hex}",
            request_payload={"problem": "p"},
        )
        assert interaction.status == "sent"
        done = await repo.mark_completed(
            interaction.id, response_payload={"summary": "ok"}
        )
        assert done.status == "completed"

    async def test_execution_job_sent_to_failed(self, test_db, _ids):
        from app.repositories.sql_execution_job_repository import (
            SqlExecutionJobRepository,
        )

        user_id, question_id = _ids
        repo = SqlExecutionJobRepository(test_db)
        job = await repo.create_sent(
            user_id=user_id,
            question_id=question_id,
            language="python",
            code_hash="ch",
            idempotency_key=f"idem-{uuid.uuid4().hex}",
            request_payload={"code": "print('hi')"},
        )
        assert job.status == "sent"
        failed = await repo.mark_failed(
            job.id, error_code="TIMEOUT", error_message="piston timeout"
        )
        assert failed.status == "failed"
