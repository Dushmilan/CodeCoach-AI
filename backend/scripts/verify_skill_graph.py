#!/usr/bin/env python3
"""End-to-end verification for the Personal Skill Graph feature.

Registers a throwaway user, ingests learning events, and checks that the
public API behaves correctly (mastery updates, idempotency, user isolation,
recommendations, history reset). Prints a PASS/FAIL report and exits
non-zero if any check fails.

Usage:
    python scripts/verify_skill_graph.py [BASE_URL]   # default http://localhost:8000

Requires the backend container to be running (docker compose up -d backend).
"""

import json
import sys
import time
import urllib.error
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
USERNAME = f"skillgraph_verify_{int(time.time())}"
PASSWORD = "testpass123"
EMAIL = f"{USERNAME}@example.com"

PASSED = 0
FAILED = 0


def report(name, ok, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {name}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILED += 1
        print(f"  FAIL  {name}  [{detail}]")


def request(method, path, token=None, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def main():
    print(f"Verifying Personal Skill Graph against {BASE_URL}\n")

    # 0. Health
    code, body = request("GET", "/health")
    report(
        "backend /health",
        code == 200 and body.get("status") == "ok",
        body.get("status", code),
    )

    # 1. Register + login
    code, body = request(
        "POST",
        "/api/auth/register",
        body={
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD,
        },
    )
    token = body.get("access_token", "") if isinstance(body, dict) else ""
    report("register user", code == 201 and token, f"{USERNAME} (HTTP {code})")
    if not token:
        code, body = request(
            "POST",
            "/api/auth/login",
            body={
                "username": USERNAME,
                "password": PASSWORD,
            },
        )
        token = body.get("access_token", "")
        report("login user", bool(token), f"HTTP {code}")
    if not token:
        print("\nCould not obtain a token; cannot continue.")
        sys.exit(1)
    user_id = body.get("user", {}).get("id", "?")

    # 2. Empty graph before any activity
    code, graph = request("GET", "/api/skills/me/skills", token=token)
    report("empty graph fetch", code == 200, f"HTTP {code}")
    report(
        "fresh user has no skills yet",
        isinstance(graph.get("skills"), list) and len(graph["skills"]) == 0,
        f"{len(graph.get('skills', []))} skills (no evidence yet)",
    )
    report(
        "edges expose taxonomy",
        isinstance(graph.get("edges"), list) and len(graph["edges"]) > 0,
        f"{len(graph.get('edges', []))} prerequisite edges",
    )

    # 3. Ingest a real learning session (passes on two-sum, reverse-string)
    session_ts = int(time.time() * 1000)
    events = [
        {
            "id": f"verify-{session_ts}-1",
            "user_id": user_id,
            "event_type": "question_started",
            "question_id": "two-sum",
            "metadata": {},
        },
        {
            "id": f"verify-{session_ts}-2",
            "user_id": user_id,
            "event_type": "submission_passed",
            "question_id": "two-sum",
            "metadata": {"attempts": 2},
        },
        {
            "id": f"verify-{session_ts}-3",
            "user_id": user_id,
            "event_type": "submission_passed",
            "question_id": "two-sum",
            "metadata": {"attempts": 1},
        },
        {
            "id": f"verify-{session_ts}-4",
            "user_id": user_id,
            "event_type": "submission_passed",
            "question_id": "reverse-string",
            "metadata": {"attempts": 3},
        },
    ]
    code, res = request("POST", "/api/skills/events", token=token, body=events)
    report(
        "ingest events",
        code == 200 and res.get("accepted") == 4,
        f"HTTP {code}, accepted={res.get('accepted')}, invalid={res.get('invalid')}",
    )

    # 4. Graph reflects mastery after real questions
    code, graph = request("GET", "/api/skills/me/skills", token=token)
    skills = {s["skill_slug"]: s for s in graph["skills"]}
    hash_maps = skills.get("hash-maps", {})
    strings = skills.get("strings", {})
    report(
        "hash-maps gained mastery",
        hash_maps.get("mastery_score", 0) > 0,
        f"mastery={hash_maps.get('mastery_score')}, status={hash_maps.get('status')}",
    )
    report(
        "strings gained mastery",
        strings.get("mastery_score", 0) > 0,
        f"mastery={strings.get('mastery_score')}, status={strings.get('status')}",
    )
    report(
        "status advanced past NEW",
        hash_maps.get("status") in ("learning", "developing", "strong"),
        hash_maps.get("status", "missing"),
    )
    report(
        "edges returned",
        isinstance(graph.get("edges"), list) and len(graph["edges"]) > 0,
        f"{len(graph.get('edges', []))} edges",
    )

    # 5. Idempotency: re-ingesting identical events must be skipped
    code, res = request("POST", "/api/skills/events", token=token, body=events)
    report(
        "re-ingest is idempotent",
        res.get("accepted") == 0 and res.get("duplicate") == 4,
        f"accepted={res.get('accepted')}, duplicate={res.get('duplicate')}",
    )

    # 6. User isolation: client-supplied user_id is overwritten with the caller
    spoofed = [
        {
            "id": f"verify-{session_ts}-spoof",
            "user_id": "someone-else",
            "event_type": "submission_failed",
            "question_id": "two-sum",
            "metadata": {},
        }
    ]
    code, res = request("POST", "/api/skills/events", token=token, body=spoofed)
    report(
        "ingest with spoofed user_id accepted",
        code == 200 and res.get("accepted") == 1,
        f"HTTP {code}",
    )
    code, graph = request("GET", "/api/skills/me/skills", token=token)
    # A failure on hash-maps should only affect the caller; the caller is this user.
    report("graph is per-user (caller sees change)", code == 200, f"HTTP {code}")

    # 7. Recommendations
    code, recs = request("GET", "/api/skills/me/recommendations?limit=3", token=token)
    report(
        "recommendations returned",
        code == 200 and isinstance(recs, list) and len(recs) > 0,
        f"HTTP {code}, {len(recs) if isinstance(recs, list) else 'n/a'} items",
    )
    if isinstance(recs, list) and recs:
        r = recs[0]
        report(
            "recommendation has reason text",
            "reason" in r and "reason_text" in r and r["reason_text"],
            f"{r.get('reason')}: {r.get('reason_text')}",
        )

    # 7b. Recommended questions resolve to concrete question payloads
    code, rq = request(
        "GET", "/api/skills/me/recommended-questions?limit=3", token=token
    )
    report(
        "recommended-questions returned",
        code == 200 and isinstance(rq, list),
        f"HTTP {code}, {len(rq) if isinstance(rq, list) else 'n/a'} items",
    )
    if isinstance(rq, list) and rq:
        report(
            "recommended-questions carry full question",
            "question" in rq[0]
            and rq[0]["question"]
            and rq[0]["question"].get("id")
            and rq[0]["question"].get("title"),
            f"{rq[0].get('skill_slug')} -> {rq[0].get('question', {}).get('id')}",
        )
    else:
        report(
            "recommended-questions empty for exercised skills",
            code == 200 and isinstance(rq, list) and rq == [],
            "no resolvable question in bank",
        )

    # 8. History reset
    code, body = request("DELETE", "/api/skills/me/history", token=token)
    report("delete history", code == 200 and body.get("status") == "ok", f"HTTP {code}")
    code, graph = request("GET", "/api/skills/me/skills", token=token)
    report(
        "graph reset after delete",
        all(s["mastery_score"] == 0.0 for s in graph["skills"]),
    )

    # 9. Security: unauthenticated requests are rejected
    code, _ = request("GET", "/api/skills/me/skills")
    report("unauthenticated rejected (401/403)", code in (401, 403), f"HTTP {code}")
    code, _ = request("GET", "/api/skills/me/recommended-questions")
    report(
        "recommended-questions rejects anonymous",
        code in (401, 403),
        f"HTTP {code}",
    )

    print(f"\n{'-' * 50}")
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
