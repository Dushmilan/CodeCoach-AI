"""RED: stale sent-state recovery must flip stuck rows to terminal states.

A crashed process can leave coaching/execution/submission rows in sent
past the recovery window. The worker marks them timeout/failed so they
never stay stuck and remain observable.
"""

import uuid
from datetime import datetime, timedelta, timezone

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
            username=f"rec{uid[:8]}",
            email=f"rec{uid[:8]}@example.com",
            hashed_password="hash",
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
    )
    await test_db.commit()
    qid = f"q-rec-{uid[:8]}"
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


async def _backdate(test_db, table: str, row_id: str, days: int = 1):
    from sqlalchemy import text

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    await test_db.execute(
        text(f"UPDATE {table} SET created_at=:ts WHERE id=:id"),
        {"ts": cutoff, "id": row_id},
    )
    await test_db.commit()


class TestStaleRecovery:
    async def test_recovers_stale_coaching_sent(self, test_db, _ids):
        from app.repositories.sql_coaching_interaction_repository import (
            SqlCoachingInteractionRepository,
        )
        from app.services.adapter_state_recovery import recover_stale_adapter_state

        user_id, question_id = _ids
        repo = SqlCoachingInteractionRepository(test_db)
        stale = await repo.create_sent(
            user_id=user_id,
            question_id=question_id,
            mode="hint",
            language="python",
            problem_hash="ph",
            code_hash="ch",
            idempotency_key=f"idem-{uuid.uuid4().hex}",
            request_payload={},
        )
        fresh = await repo.create_sent(
            user_id=user_id,
            question_id=question_id,
            mode="hint",
            language="python",
            problem_hash="ph",
            code_hash="ch",
            idempotency_key=f"idem-{uuid.uuid4().hex}",
            request_payload={},
        )
        done = await repo.mark_completed(stale.id, response_payload={"ok": True})
        assert done.status == "completed"
        await _backdate(test_db, "coaching_interactions", stale.id)
        # Re-create stale as sent (completed row must stay untouched).
        stale2 = await repo.create_sent(
            user_id=user_id,
            question_id=question_id,
            mode="hint",
            language="python",
            problem_hash="ph",
            code_hash="ch",
            idempotency_key=f"idem-{uuid.uuid4().hex}",
            request_payload={},
        )
        await _backdate(test_db, "coaching_interactions", stale2.id)

        counts = await recover_stale_adapter_state(
            test_db, older_than_minutes=60, limit=100
        )

        assert counts["coaching_interactions"] >= 1
        recovered = await repo.get(stale2.id)
        assert recovered is not None and recovered.status == "timeout"
        untouched = await repo.get(fresh.id)
        assert untouched is not None and untouched.status == "sent"

    async def test_recovers_stale_execution_and_submission(self, test_db, _ids):
        from app.models.submission_schemas import SubmissionIn
        from app.repositories.sql_execution_job_repository import (
            SqlExecutionJobRepository,
        )
        from app.repositories.sql_submission_repository import (
            SqlSubmissionRepository,
        )
        from app.services.adapter_state_recovery import recover_stale_adapter_state

        user_id, question_id = _ids
        jobs = SqlExecutionJobRepository(test_db)
        subs = SqlSubmissionRepository(test_db)
        job = await jobs.create_sent(
            user_id=user_id,
            question_id=question_id,
            language="python",
            code_hash="ch",
            idempotency_key=f"idem-{uuid.uuid4().hex}",
            request_payload={},
        )
        sent = await subs.create_sent(
            user_id=user_id,
            submission=SubmissionIn(
                question_id=question_id, code="x", language="python", passed=False
            ),
        )
        await _backdate(test_db, "execution_jobs", job.id)
        await _backdate(test_db, "submissions", sent.id)

        counts = await recover_stale_adapter_state(
            test_db, older_than_minutes=60, limit=100
        )

        assert counts["execution_jobs"] >= 1
        assert counts["submissions"] >= 1
        assert (await jobs.get(job.id)).status == "timeout"  # type: ignore[union-attr]
        assert (await subs.get(sent.id)).status == "failed"  # type: ignore[union-attr]
