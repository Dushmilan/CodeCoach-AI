# CodeCoach AI — Goal

## Mission
An open-source LeetCode alternative for university students. Practice coding interview questions with instant feedback, AI coaching, and progress tracking — all powered by NVIDIA's free-tier API.

## Target Audience
- University students preparing for technical interviews
- Self-taught programmers looking for structured practice
- Anyone wanting a free, private coding practice platform

## Design Pillars

1. **Zero-cost to students** — NVIDIA free-tier API for AI coaching, Piston for code execution (self-hosted), Supabase free tier for optional auth.
2. **Clean architecture** — Ports/adapters pattern on the backend, dependency-injected services on the frontend. Easy to extend, easy to test.
3. **Student-first UX** — Two-button workflow (Run → see visible test cases, Submit → all test cases including hidden). Progress persists in localStorage. No account required to start.
4. **Three languages from day one** — Python, JavaScript, Java.
5. **AI coaching is a feature, not the product** — The question bank and test runner are the core. Coaching augments, not replaces, the learning process.

## Non-Goals
- Not a competitive programming platform (no leaderboards, contests, or ratings)
- Not a code execution marketplace (no server-side code storage, no multi-tenant execution)
- Not a full LMS (no course management, grading rubrics, or class rosters)

## Success Criteria
- Students can browse questions, write code in 3 languages, run/submit tests, and get AI coaching — all without paying or creating an account.
- The entire platform can be `docker compose up`'d by a university CS club advisor.
- A student who solves 50 questions across 3 difficulty levels is interview-ready for FAANG-adjacent roles.
