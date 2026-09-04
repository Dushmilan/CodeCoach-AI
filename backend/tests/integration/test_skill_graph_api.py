"""API integration tests for the skill-graph endpoints."""

from fastapi.testclient import TestClient

from tests.fixtures.auth_helpers import register_headers


class TestSkillGraphAPI:
    def test_me_skills_requires_auth(self, test_client: TestClient):
        res = test_client.get("/api/skills/me/skills")
        assert res.status_code == 401

    def test_me_skills_empty_for_new_user(self, test_client: TestClient):
        headers = register_headers(test_client, "skillempty")
        res = test_client.get("/api/skills/me/skills", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["skills"] == []
        assert "edges" in data

    def test_recommendations_empty_for_new_user(self, test_client: TestClient):
        headers = register_headers(test_client, "skillrecempty")
        res = test_client.get("/api/skills/me/recommendations", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_ingest_event_then_read_graph(self, test_client: TestClient):
        headers = register_headers(test_client, "skillsolve")
        event = {
            "id": "api-event-1",
            "user_id": "nobody",  # server normalizes to the caller
            "event_type": "submission_passed",
            "question_id": "two-sum",
            "metadata": {},
            "occurred_at": "2026-08-01T09:00:00Z",
        }
        res = test_client.post("/api/skills/events", headers=headers, json=[event])
        assert res.status_code == 200
        data = res.json()
        assert data["accepted"] == 1
        assert data["invalid"] == 0

        graph = test_client.get("/api/skills/me/skills", headers=headers)
        assert graph.status_code == 200

    def test_foreign_user_id_normalized_to_caller(self, test_client: TestClient):
        """A client-supplied user_id is never trusted: it is overwritten with
        the authenticated caller, so no cross-user write can happen."""
        headers_a = register_headers(test_client, "usera")
        headers_b = register_headers(test_client, "userb")
        event = {
            "id": "api-event-foreign",
            "user_id": "somebody-else",
            "event_type": "submission_passed",
            "question_id": "two-sum",
            "metadata": {},
            "occurred_at": "2026-08-01T09:00:00Z",
        }
        res = test_client.post("/api/skills/events", headers=headers_a, json=[event])
        assert res.status_code == 200
        assert res.json()["accepted"] == 1
        assert res.json()["invalid"] == 0

        # userb never receives usera's history.
        graph_b = test_client.get("/api/skills/me/skills", headers=headers_b)
        assert graph_b.json()["skills"] == []

    def test_delete_history(self, test_client: TestClient):
        headers = register_headers(test_client, "skilldelete")
        event = {
            "id": "api-event-del",
            "user_id": "nobody",
            "event_type": "submission_passed",
            "question_id": "two-sum",
            "metadata": {},
            "occurred_at": "2026-08-01T09:00:00Z",
        }
        assert (
            test_client.post(
                "/api/skills/events", headers=headers, json=[event]
            ).json()["accepted"]
            == 1
        )
        res = test_client.delete("/api/skills/me/history", headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
        graph = test_client.get("/api/skills/me/skills", headers=headers)
        assert graph.json()["skills"] == []

    def test_recommended_questions_requires_auth(self, test_client: TestClient):
        res = test_client.get("/api/skills/me/recommended-questions")
        assert res.status_code == 401

    def test_recommended_questions_empty_for_new_user(self, test_client: TestClient):
        headers = register_headers(test_client, "skillrqempty")
        res = test_client.get("/api/skills/me/recommended-questions", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_recommended_questions_after_activity(self, test_client: TestClient):
        """After solving questions, the endpoint returns recommendations that
        carry a fully-resolved Question payload."""
        headers = register_headers(test_client, "skillrqsolve")
        events = [
            {
                "id": f"api-rq-{i}",
                "user_id": "nobody",
                "event_type": "submission_passed",
                "question_id": "two-sum",
                "metadata": {},
                "occurred_at": "2026-08-01T09:00:00Z",
            }
            for i in range(2)
        ]
        res = test_client.post("/api/skills/events", headers=headers, json=events)
        assert res.status_code == 200
        assert res.json()["accepted"] == 2

        # Seed question_skills via the REAL idempotent seed path so this guard
        # breaks if the seed pipeline or taxonomy coverage regresses.
        import asyncio

        from scripts.seed_skill_graph import seed

        asyncio.run(seed())

        res = test_client.get(
            "/api/skills/me/recommended-questions?limit=5", headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        # F3 regression guard: solving a fully-mapped bank question MUST yield
        # at least one recommendation (empty output means the mapping or seed
        # pipeline broke).
        assert len(data) >= 1, (
            "expected non-empty recommendations after solving a mapped "
            "question - check QUESTION_SKILLS coverage and question_skills seed"
        )
        exercised_skills = {"hash-maps", "arrays"}
        assert any(item["skill_slug"] in exercised_skills for item in data), (
            f"recommendations should target the exercised skills "
            f"{exercised_skills}, got {[i['skill_slug'] for i in data]}"
        )
        # The suggested question for the exercised skill must resolve to a real
        # question object (id + title present) when one exists in the bank.
        for item in data:
            assert item["skill_slug"]
            assert item["reason_text"]
            assert "question" in item
            if item["question"]:
                assert item["question"]["id"]
                assert item["question"]["title"]
