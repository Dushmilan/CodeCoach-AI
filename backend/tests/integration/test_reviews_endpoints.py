"""Integration tests for spaced-repetition review endpoints (/api/reviews)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.models.mistake_schemas import ReviewCard
from app.models.schemas import Question
from app.repositories.sql_question_repository import SqlQuestionRepository
from app.repositories.sql_review_repository import SqlReviewRepository
from tests.fixtures.auth_helpers import register_user_headers

NOW = datetime.now(timezone.utc)


async def _ensure_question(test_db, sample_question_data) -> str:
    """test_db wipes seeded rows: insert a parent question for card FKs."""
    from sqlalchemy.exc import IntegrityError

    qid = f"rev-q-{uuid.uuid4().hex[:8]}"
    data = dict(sample_question_data)
    data["id"] = qid
    await SqlQuestionRepository(test_db).add(Question(**data))
    try:
        await test_db.commit()
    except IntegrityError:
        await test_db.rollback()
    return qid


def _card(
    user_id: str, question_id: str, due_in_days: int = -1, tag: str = "foo"
) -> ReviewCard:
    now = datetime.now(timezone.utc)
    return ReviewCard(
        id=f"card-{uuid.uuid4().hex[:10]}",
        user_id=user_id,
        question_id=question_id,
        error_signature=f"TypeError:{tag}",
        state="scheduled",
        ease=2.5,
        interval_days=1,
        repetitions=1,
        lapses=0,
        due_at=now + timedelta(days=due_in_days),
        last_reviewed_at=None,
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )


@pytest.mark.asyncio
async def test_due_empty_for_new_user(test_client: TestClient):
    _, headers = register_user_headers(test_client, f"rev-{uuid.uuid4().hex[:8]}")
    res = test_client.get("/api/reviews/due", headers=headers)
    assert res.status_code == 200
    assert res.json() == {"cards": [], "total": 0}


@pytest.mark.asyncio
async def test_due_returns_only_matured_cards(
    test_client: TestClient, test_db, sample_question_data
):
    uid, headers = register_user_headers(test_client, f"rev-{uuid.uuid4().hex[:8]}")
    qid = await _ensure_question(test_db, sample_question_data)
    repo = SqlReviewRepository(test_db)
    due_card = _card(uid, qid, due_in_days=-1, tag="due")
    future_card = _card(uid, qid, due_in_days=30, tag="future")
    await repo.save(due_card)
    await repo.save(future_card)
    await test_db.commit()

    res = test_client.get("/api/reviews/due", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["cards"][0]["id"] == due_card.id


@pytest.mark.asyncio
async def test_grade_advances_schedule(
    test_client: TestClient, test_db, sample_question_data
):
    uid, headers = register_user_headers(test_client, f"rev-{uuid.uuid4().hex[:8]}")
    qid = await _ensure_question(test_db, sample_question_data)
    repo = SqlReviewRepository(test_db)
    card = _card(uid, qid, due_in_days=-1)
    await repo.save(card)
    await test_db.commit()

    res = test_client.post(
        f"/api/reviews/{card.id}/grade", json={"quality": 4}, headers=headers
    )
    assert res.status_code == 200
    graded = res.json()["card"]
    assert graded["repetitions"] == 2

    # No longer due immediately.
    due = test_client.get("/api/reviews/due", headers=headers)
    assert due.json()["total"] == 0


@pytest.mark.asyncio
async def test_grade_unknown_card_returns_404(test_client: TestClient):
    _, headers = register_user_headers(test_client, f"rev-{uuid.uuid4().hex[:8]}")
    res = test_client.post(
        "/api/reviews/no-such-card/grade", json={"quality": 4}, headers=headers
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_grade_invalid_quality_rejected(test_client: TestClient):
    _, headers = register_user_headers(test_client, f"rev-{uuid.uuid4().hex[:8]}")
    res = test_client.post(
        "/api/reviews/any-card/grade", json={"quality": 9}, headers=headers
    )
    assert res.status_code == 422


def test_due_requires_auth(test_client: TestClient):
    assert test_client.get("/api/reviews/due").status_code in (401, 403)
