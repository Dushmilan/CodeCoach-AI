from __future__ import annotations

from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, List, Optional

from app.models.schemas import Difficulty, Question
from app.models.skill_graph_schemas import (
    EventIngestResult,
    LearningEvent,
    QuestionSkill,
    Recommendation,
    RecommendedQuestion,
    Skill,
    SkillGraphEdge,
    SkillGraphResponse,
    SkillSummary,
    UserSkillState,
)
from app.ports.skill_graph_repository import SkillGraphRepository
from app.ports.submission_repository import SubmissionRepository
from app.models.skill_graph_schemas import SkillStatus, Trend, RecommendationReason

from app.services.skill_graph_rules import (
    apply_event,
    cold_start_order,
    decay_state,
    mastery_for_status,
    recommend,
)
from app.services.skill_taxonomy import (
    DEFAULT_COLD_START_QUESTION_IDS,
    SUPPORTING_SKILL_SLUGS,
)


class SkillGraphService:
    """Orchestrates the deterministic Personal Skill Graph.

    Pure rule logic lives in ``skill_graph_rules``; this service wires events
    to skills (via question mappings or explicit slugs), persists them, and
    derives the graph + recommendations. No ML anywhere in this path.
    """

    # Difficulty ordering for the attempted-easier fill (Issue #233).
    # Question.difficulty is a required enum on every Question, so strict
    # rank comparison is the reliable "easier" signal — no programme-order
    # fallback is needed.
    _DIFFICULTY_RANK = {
        Difficulty.EASY: 0,
        Difficulty.MEDIUM: 1,
        Difficulty.HARD: 2,
    }

    # Loader fan-out bounds for the attempted-easier fill (Round 2).
    # Uncapped, one unsolved attempt costs one ``question_loader`` call per
    # same-skill candidate, so a many-attempts user costs
    # ``attempts × candidates`` loader calls. Both bounds keep best-pick
    # (easiest strictly-easier, id tiebreak) in unsolved-attempt order and
    # never let the fill exceed the caller's limit.
    #
    # Fair-share (Round 3): the scan is newest-attempt-first against a single
    # shared budget, so the newest attempts could consume the whole budget
    # and starve older attempts of any candidate scan. Each attempt's
    # candidate allowance is therefore its even share of the remaining
    # budget after reserving one call per not-yet-scanned attempt's own
    # question load — every unsolved attempt gets a scan, best-pick and
    # attempt order are unchanged.
    _ATTEMPTED_FILL_MAX_LOADER_CALLS = 50
    _ATTEMPTED_FILL_MAX_CANDIDATE_LOADS_PER_ATTEMPT = 20

    def __init__(
        self,
        repository: SkillGraphRepository,
        submission_repository: Optional[SubmissionRepository] = None,
    ):
        self.repository = repository
        self._submission_repository = submission_repository

    async def _load_taxonomy(
        self,
    ) -> tuple[Dict[str, Skill], Dict[str, List[QuestionSkill]]]:
        skills = await self.repository.list_skills()
        question_skills = await self.repository.get_question_skills()
        skills_by_slug = {s.slug: s for s in skills}
        question_skills_by_q: Dict[str, List[QuestionSkill]] = {}
        for qs in question_skills:
            question_skills_by_q.setdefault(qs.question_id, []).append(qs)
        return skills_by_slug, question_skills_by_q

    @staticmethod
    def _attributed_skills(
        event: LearningEvent,
        skills_by_slug: Dict[str, Skill],
        question_skills_by_q: Dict[str, List[QuestionSkill]],
    ) -> List[QuestionSkill]:
        """Resolve which skills an event touches.

        Explicit skill_slug wins; otherwise the question's skill mapping is
        used; an unmapped question attributes to nothing (cannot corrupt the
        graph).
        """
        if event.skill_slug:
            if event.skill_slug in skills_by_slug:
                return [
                    QuestionSkill(
                        question_id=event.question_id or "",
                        skill_slug=event.skill_slug,
                        weight=1.0,
                    )
                ]
            return []
        if event.question_id:
            return question_skills_by_q.get(event.question_id, [])
        return []

    async def ingest_events(
        self, events: List[LearningEvent], user_id: Optional[str] = None
    ) -> EventIngestResult:
        skills_by_slug, question_skills_by_q = await self._load_taxonomy()
        result = EventIngestResult()

        for event in events:
            if user_id and event.user_id != user_id:
                result.invalid += 1
                continue
            if not event.id:
                result.skipped += 1
                continue
            if await self.repository.event_exists(event.id):
                result.duplicate += 1
                continue

            attributed = self._attributed_skills(
                event, skills_by_slug, question_skills_by_q
            )

            await self.repository.save_event(event)
            result.accepted += 1

            if attributed:
                states = await self.repository.get_states(event.user_id)
                for mapping in attributed:
                    state = states.get(mapping.skill_slug)
                    if state is None:
                        state = UserSkillState(
                            user_id=event.user_id, skill_slug=mapping.skill_slug
                        )
                    new_state = apply_event(state, event)
                    await self.repository.save_state(new_state)

        return result

    async def get_graph(
        self,
        user_id: str,
        now: Optional[datetime] = None,
        include_boilerplate: bool = False,
    ) -> SkillGraphResponse:
        now = now or datetime.now(timezone.utc)
        skills_by_slug, _ = await self._load_taxonomy()
        states = await self.repository.get_states(user_id)

        summaries: List[SkillSummary] = []
        for slug, skill in skills_by_slug.items():
            state = states.get(slug)
            if state is None:
                if not include_boilerplate:
                    continue
                summaries.append(
                    SkillSummary(
                        skill_slug=slug,
                        name=skill.name,
                        mastery_score=0.0,
                        confidence=0.0,
                        status=SkillStatus.NEW,
                        trend=Trend.STABLE,
                        evidence_count=0,
                        recent_error_count=0,
                        last_seen_at=None,
                        last_reviewed_at=None,
                    )
                )
                continue
            decayed = decay_state(state, now)
            summaries.append(
                SkillSummary(
                    skill_slug=slug,
                    name=skill.name,
                    mastery_score=round(decayed.mastery_score, 3),
                    confidence=round(decayed.confidence, 3),
                    # Status is always derived from mastery (never from a
                    # stored value that could be stale), so thresholds stay
                    # authoritative.
                    status=mastery_for_status(decayed.mastery_score),
                    trend=decayed.trend,
                    evidence_count=decayed.evidence_count,
                    recent_error_count=decayed.recent_error_count,
                    last_seen_at=decayed.last_seen_at,
                    last_reviewed_at=decayed.last_reviewed_at,
                )
            )
        # Boilerplate-first: stable learners see full taxonomy sorted by mastery;
        # new users (all 0.0) keep taxonomy insertion order.
        if include_boilerplate:
            summaries.sort(key=lambda s: (-s.mastery_score, s.skill_slug))
        else:
            summaries.sort(key=lambda s: s.mastery_score, reverse=True)

        edges = [
            SkillGraphEdge(source=prereq, target=slug, relation="prerequisite")
            for slug, skill in skills_by_slug.items()
            for prereq in skill.prerequisite_ids
            if prereq in skills_by_slug
        ]
        return SkillGraphResponse(skills=summaries, edges=edges)

    async def get_boilerplate_graph(self) -> SkillGraphResponse:
        """Deterministic boilerplate graph — no user state, all skills NEW.

        Used for onboarding previews and unauthenticated tour. Pure taxonomy,
        no DB state reads beyond the skill list.
        """
        skills_by_slug, _ = await self._load_taxonomy()
        summaries = [
            SkillSummary(
                skill_slug=slug,
                name=skill.name,
                mastery_score=0.0,
                confidence=0.0,
                status=SkillStatus.NEW,
                trend=Trend.STABLE,
                evidence_count=0,
                recent_error_count=0,
                last_seen_at=None,
                last_reviewed_at=None,
            )
            for slug, skill in skills_by_slug.items()
        ]
        summaries.sort(key=lambda s: s.skill_slug)
        edges = [
            SkillGraphEdge(source=prereq, target=slug, relation="prerequisite")
            for slug, skill in skills_by_slug.items()
            for prereq in skill.prerequisite_ids
            if prereq in skills_by_slug
        ]
        return SkillGraphResponse(skills=summaries, edges=edges)

    async def get_roadmap(
        self, user_id: str, now: Optional[datetime] = None
    ) -> SkillGraphResponse:
        """Roadmap-track graph: supporting skills excluded from progress totals.

        Full per-skill state stays available via ``get_graph`` (analytics /
        coaching context); this view is what the NeetCode-style roadmap renders.
        """
        full = await self.get_graph(user_id, now=now)
        supporting = set(SUPPORTING_SKILL_SLUGS)
        roadmap_skills = [s for s in full.skills if s.skill_slug not in supporting]
        roadmap_edges = [
            e
            for e in full.edges
            if e.source not in supporting and e.target not in supporting
        ]
        return SkillGraphResponse(skills=roadmap_skills, edges=roadmap_edges)

    async def get_recommendations(
        self,
        user_id: str,
        now: Optional[datetime] = None,
        limit: int = 5,
        include_supporting: bool = False,
    ) -> List[Recommendation]:
        now = now or datetime.now(timezone.utc)
        skills_by_slug, question_skills_by_q = await self._load_taxonomy()
        if not include_supporting:
            supporting = set(SUPPORTING_SKILL_SLUGS)
            skills_by_slug = {
                slug: s for slug, s in skills_by_slug.items() if slug not in supporting
            }
        states = await self.repository.get_states(user_id)

        skill_names = {slug: s.name for slug, s in skills_by_slug.items()}
        prerequisites = {slug: s.prerequisite_ids for slug, s in skills_by_slug.items()}
        question_by_skill: Dict[str, List[str]] = {}
        for question_id, mappings in question_skills_by_q.items():
            for m in mappings:
                question_by_skill.setdefault(m.skill_slug, []).append(question_id)

        return recommend(
            states=states,
            skill_names=skill_names,
            prerequisites=prerequisites,
            question_by_skill=question_by_skill,
            now=now,
            limit=limit,
        )

    async def get_enrolled_programme_starters(
        self, user_id: str, limit: int = 5
    ) -> List[str]:
        return await self.repository.get_enrolled_programme_starters(
            user_id, limit=limit
        )

    @staticmethod
    async def _resolve_ids(
        question_ids: List[str],
        skill_slug: str,
        skill_name: str,
        reason_text: str,
        question_loader: Callable[[str], Awaitable[Optional[Question]]],
    ) -> List[RecommendedQuestion]:
        """Resolve IDs via the loader, skipping unresolvable ones.

        Never fabricates practice data: an ID the loader cannot resolve is
        dropped, not synthesized.
        """
        resolved: List[RecommendedQuestion] = []
        for question_id in question_ids:
            question = await question_loader(question_id)
            if question is None:
                continue
            resolved.append(
                RecommendedQuestion(
                    skill_slug=skill_slug,
                    skill_name=skill_name,
                    reason=RecommendationReason.NEW_SKILL,
                    reason_text=reason_text,
                    question=question,
                )
            )
        return resolved

    async def get_recommended_questions(
        self,
        user_id: str,
        question_loader: Callable[[str], Awaitable[Optional[Question]]],
        limit: int = 5,
        now: Optional[datetime] = None,
    ) -> List[RecommendedQuestion]:
        """Recommendations enriched with the concrete practice question.

        ``question_loader`` resolves a question ID to a full ``Question`` (or
        ``None``). Recommendations whose question cannot be resolved are
        skipped — the response never fabricates practice data.

        Cold-start (Issue #186): when skill-graph recs resolve to nothing and
        the user has no skill states, fall back to the enrolled programme's
        starter questions in deterministic programme order.

        Empty-state default (Issue #232): when the user also has no enrolled
        programme starters (brand-new user, no classroom), fall back to the
        curated DEFAULT_COLD_START_QUESTION_IDS so whats-next is never empty.
        Both fallbacks resolve via ``question_loader`` and skip unresolvable
        IDs — the response never fabricates practice data.
        """
        recs = await self.get_recommendations(user_id, now=now, limit=limit)
        results: List[RecommendedQuestion] = []
        for rec in recs:
            question_id = rec.suggested_question_id
            if not question_id:
                continue
            question = await question_loader(question_id)
            if question is None:
                continue
            results.append(
                RecommendedQuestion(
                    skill_slug=rec.skill_slug,
                    skill_name=rec.name,
                    reason=rec.reason,
                    reason_text=rec.reason_text,
                    question=question,
                )
            )
        if len(results) < limit:
            seen_ids = {r.question.id for r in results}
            results.extend(
                await self._attempted_easier_fill(
                    user_id,
                    question_loader,
                    exclude_ids=seen_ids,
                    remaining=limit - len(results),
                )
            )
        if not results:
            states = await self.repository.get_states(user_id)
            if not states:
                starter_ids = cold_start_order(
                    await self.get_enrolled_programme_starters(user_id, limit=limit),
                    limit=limit,
                )
                results.extend(
                    await self._resolve_ids(
                        starter_ids,
                        "programme-start",
                        "Programme Start",
                        "Start your programme.",
                        question_loader,
                    )
                )
                if not results:
                    default_ids = cold_start_order(
                        list(DEFAULT_COLD_START_QUESTION_IDS),
                        limit=limit,
                    )
                    results.extend(
                        await self._resolve_ids(
                            default_ids,
                            "getting-started",
                            "Getting Started",
                            "Start with these foundational questions.",
                            question_loader,
                        )
                    )
        return results

    async def _attempted_easier_fill(
        self,
        user_id: str,
        question_loader: Callable[[str], Awaitable[Optional[Question]]],
        exclude_ids: set[str],
        remaining: int,
    ) -> List[RecommendedQuestion]:
        """Recommend easier same-skill questions for unsolved attempts (Issue #233).

        Source is ``SubmissionRepository.list_by_user`` (newest-first):
        distinct attempted ids with NO passed attempt map to a skill via
        ``question_skills`` (highest-weight mapping wins), and each yields the
        easiest same-skill question that is strictly easier than the attempt,
        not already attempted, not already recommended, and resolvable via
        ``question_loader``. If the attempted question itself cannot be
        resolved, the comparison rank is unknown and the easiest same-skill
        candidate is used. Fills remaining slots only; never exceeds the
        caller's limit. Loader fan-out is bounded (fair-share per-attempt
        candidate loads + total budget, rank-0 early exit); best-pick and
        unsolved-attempt order are unchanged. Runs AFTER skill recs and
        BEFORE programme starters.
        """
        submissions_repo = self._submission_repository
        if submissions_repo is None or remaining <= 0:
            return []
        submissions = await submissions_repo.list_by_user(user_id, limit=100)
        if not submissions:
            return []
        solved_ids = {s.question_id for s in submissions if s.passed}
        attempted_ordered: List[str] = []
        for s in submissions:
            if s.question_id and s.question_id not in attempted_ordered:
                attempted_ordered.append(s.question_id)
        unsolved = [qid for qid in attempted_ordered if qid not in solved_ids]
        if not unsolved:
            return []

        skills_by_slug, question_skills_by_q = await self._load_taxonomy()
        question_by_skill: Dict[str, List[str]] = {}
        for question_id, mappings in question_skills_by_q.items():
            for m in mappings:
                question_by_skill.setdefault(m.skill_slug, []).append(question_id)

        attempted_set = set(attempted_ordered)
        seen = set(exclude_ids)
        results: List[RecommendedQuestion] = []
        loader_calls = 0
        for idx, attempted_id in enumerate(unsolved):
            if len(results) >= remaining:
                break
            if loader_calls >= self._ATTEMPTED_FILL_MAX_LOADER_CALLS:
                break
            mappings = question_skills_by_q.get(attempted_id, [])
            if not mappings:
                continue
            skill_slug = max(mappings, key=lambda m: m.weight).skill_slug
            skill = skills_by_slug.get(skill_slug)
            skill_name = skill.name if skill is not None else skill_slug
            loader_calls += 1
            attempted_question = await question_loader(attempted_id)
            attempted_rank = (
                self._DIFFICULTY_RANK.get(attempted_question.difficulty)
                if attempted_question is not None
                else None
            )
            best: Optional[Question] = None
            best_rank = 0
            candidate_loads = 0
            # Fair-share of the remaining budget across the attempts still
            # to scan (this one included), reserving one call per future
            # attempt's own question load so newer scans cannot starve
            # older ones. Never exceeds the per-attempt cap.
            attempts_left = len(unsolved) - idx
            headroom = (
                self._ATTEMPTED_FILL_MAX_LOADER_CALLS
                - loader_calls
                - (attempts_left - 1)
            )
            candidate_allowance = min(
                self._ATTEMPTED_FILL_MAX_CANDIDATE_LOADS_PER_ATTEMPT,
                max(0, headroom // attempts_left),
            )
            for candidate_id in question_by_skill.get(skill_slug, []):
                if best is not None and best_rank == 0:
                    break
                if candidate_loads >= candidate_allowance:
                    break
                if loader_calls >= self._ATTEMPTED_FILL_MAX_LOADER_CALLS:
                    break
                if candidate_id in seen or candidate_id in attempted_set:
                    continue
                candidate_loads += 1
                loader_calls += 1
                candidate = await question_loader(candidate_id)
                if candidate is None:
                    continue
                rank = self._DIFFICULTY_RANK.get(candidate.difficulty, 1)
                if attempted_rank is not None and rank >= attempted_rank:
                    continue
                if best is None or (rank, candidate.id) < (best_rank, best.id):
                    best = candidate
                    best_rank = rank
            if best is None:
                continue
            seen.add(best.id)
            results.append(
                RecommendedQuestion(
                    skill_slug=skill_slug,
                    skill_name=skill_name,
                    reason=RecommendationReason.RETRY_EASIER,
                    reason_text=(
                        f"An easier {skill_name} problem to retry after {attempted_id}."
                    ),
                    question=best,
                )
            )
        return results

    async def delete_history(self, user_id: str) -> None:
        await self.repository.delete_user_history(user_id)
