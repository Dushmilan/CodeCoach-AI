"""Deterministic rules engine for the Personal Skill Graph.

Pure functions only — no I/O, no ML. The engine derives mastery/confidence/
status/recommendations from explicit rules so behaviour is reproducible and
unit-testable. Persistence lives in repositories; orchestration in services.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.skill_graph_schemas import (
    LearningEvent,
    LearningEventType,
    Recommendation,
    RecommendationReason,
    SkillStatus,
    Trend,
    UserSkillState,
)
from app.services.skill_taxonomy import (
    CONFIDENCE_CAP,
    CONFIDENCE_PER_EVENT,
    DECAY_ENABLED,
    DECAY_FLOOR,
    DECAY_PER_DAY,
    DISTINCT_QUESTION_CEILING,
    EVIDENCE,
    HINT_PENALTY,
    MAX_INACTIVE_DAYS,
    MAX_MASTERY,
    MAX_MASTERY_DELTA_PER_EVENT,
    MIN_MASTERY,
    POSITIVE_REFERENCE,
    REPEATED_FAIL_REDUCTION,
    REVIEW_FAIL_REDUCTION,
    FAIL_REDUCTION,
    STATUS_THRESHOLDS,
)


def _clamp(value: float, low: float = MIN_MASTERY, high: float = MAX_MASTERY) -> float:
    return max(low, min(high, value))


def mastery_for_status(mastery: float) -> SkillStatus:
    for threshold, status in STATUS_THRESHOLDS:
        if mastery >= threshold:
            return status
    return SkillStatus.NEW


def derive_trend(previous_mastery: float, next_mastery: float) -> Trend:
    if next_mastery > previous_mastery + 1e-9:
        return Trend.IMPROVING
    if next_mastery < previous_mastery - 1e-9:
        return Trend.DECLINING
    return Trend.STABLE


def _evidence_for_event(event: LearningEvent) -> float:
    """Resolve the deterministic evidence delta for an event."""
    meta = event.metadata or {}
    event_type = event.event_type

    if event_type == LearningEventType.SUBMISSION_PASSED:
        if meta.get("solution_revealed"):
            return EVIDENCE["submission_passed_after_solution"]
        if (meta.get("hint_count") or 0) > 0 or meta.get("hints_used"):
            return EVIDENCE["submission_passed_after_hint"]
        return EVIDENCE["submission_passed_independent"]

    if event_type == LearningEventType.SUBMISSION_FAILED:
        if meta.get("repeated_error"):
            return EVIDENCE["repeated_error"]
        return EVIDENCE["submission_failed"]

    if event_type == LearningEventType.HINT_REQUESTED:
        return EVIDENCE["hint_requested"]
    if event_type == LearningEventType.LESSON_COMPLETED:
        return EVIDENCE["lesson_completed"]
    if event_type == LearningEventType.REVIEW_COMPLETED:
        passed = meta.get("passed", True)
        return EVIDENCE["review_passed"] if passed else EVIDENCE["review_failed"]
    if event_type == LearningEventType.DIAGNOSIS_CREATED:
        return EVIDENCE["diagnosis_created"]
    return 0.0


def _mastery_delta(event: LearningEvent) -> float:
    """Map an event to a bounded, sign-aware mastery change.

    Positive evidence scales linearly against the independent-pass reference
    so independent solves earn more credit than hinted/revealed solves without
    ever exceeding the per-event cap. Failures reduce mastery multiplicatively
    so a single slip never destroys an established skill.
    """
    event_type = event.event_type
    meta = event.metadata or {}

    if event_type == LearningEventType.SUBMISSION_FAILED:
        reduction = (
            REPEATED_FAIL_REDUCTION if meta.get("repeated_error") else FAIL_REDUCTION
        )
        return -reduction  # applied multiplicatively below

    if event_type == LearningEventType.REVIEW_COMPLETED:
        passed = meta.get("passed", True)
        if passed:
            return _positive_delta(EVIDENCE["review_passed"])
        return -REVIEW_FAIL_REDUCTION  # applied multiplicatively below

    if event_type == LearningEventType.HINT_REQUESTED:
        return -HINT_PENALTY

    return _positive_delta(_evidence_for_event(event))


def _positive_delta(evidence: float) -> float:
    if evidence <= 0:
        return 0.0
    scale = min(1.0, evidence / POSITIVE_REFERENCE)
    return MAX_MASTERY_DELTA_PER_EVENT * scale


def _apply_mastery_delta(state: UserSkillState, delta: float) -> float:
    if delta >= 0:
        return _clamp(state.mastery_score + delta)
    if delta in (-FAIL_REDUCTION, -REPEATED_FAIL_REDUCTION, -REVIEW_FAIL_REDUCTION):
        factor = 1.0 - abs(delta)
        return _clamp(state.mastery_score * factor)
    return _clamp(state.mastery_score + delta)


def _breadth_cap_from_ids(distinct_ids: List[str]) -> float:
    return DISTINCT_QUESTION_CEILING * max(1, len(distinct_ids))


def apply_event(state: UserSkillState, event: LearningEvent) -> UserSkillState:
    """Apply a single learning event to a skill state.

    Only events that can be attributed to a skill (via question mapping or an
    explicit skill_slug) should reach this function; the caller resolves the
    skill attribution. This function is idempotent by construction: callers
    dedupe events before invoking it.
    """
    is_failure = event.event_type == LearningEventType.SUBMISSION_FAILED
    is_review = event.event_type == LearningEventType.REVIEW_COMPLETED

    previous = state.mastery_score
    delta = _mastery_delta(event)
    mastery = _apply_mastery_delta(state, delta)

    distinct_ids = list(state.distinct_question_ids)
    if event.question_id and event.question_id not in distinct_ids:
        distinct_ids.append(event.question_id)
    if delta >= 0:
        mastery = _clamp(min(mastery, _breadth_cap_from_ids(distinct_ids)))

    if is_failure:
        recent_errors = state.recent_error_count + 1
    elif is_review:
        recent_errors = max(0, state.recent_error_count - 1)
    else:
        recent_errors = state.recent_error_count

    confidence = _clamp(
        state.confidence + CONFIDENCE_PER_EVENT, low=0.0, high=CONFIDENCE_CAP
    )
    if is_failure:
        confidence = _clamp(confidence - 0.1, low=0.0, high=CONFIDENCE_CAP)

    evidence_count = state.evidence_count + 1
    occurred = event.occurred_at or datetime.now(timezone.utc)

    return UserSkillState(
        user_id=state.user_id,
        skill_slug=state.skill_slug,
        mastery_score=mastery,
        confidence=confidence,
        evidence_count=evidence_count,
        recent_error_count=recent_errors,
        distinct_question_ids=distinct_ids,
        last_seen_at=occurred,
        last_reviewed_at=occurred if is_review else state.last_reviewed_at,
        status=mastery_for_status(mastery),
        trend=derive_trend(previous, mastery),
    )


def _as_utc(value: datetime) -> datetime:
    """Normalise naive datetimes (MySQL) to aware UTC for safe subtraction."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def decay_state(state: UserSkillState, now: datetime) -> UserSkillState:
    """Decay mastery/confidence based on days since the last practice."""
    if not DECAY_ENABLED:
        return state
    if state.last_seen_at is None:
        return state
    inactive_days = max(
        0.0, (_as_utc(now) - _as_utc(state.last_seen_at)).total_seconds() / 86400.0
    )
    if inactive_days <= MAX_INACTIVE_DAYS:
        return state

    decay_factor = DECAY_PER_DAY * (inactive_days - MAX_INACTIVE_DAYS)
    mastery = _clamp(state.mastery_score - decay_factor, low=DECAY_FLOOR)
    confidence = _clamp(state.confidence - decay_factor, low=0.0, high=CONFIDENCE_CAP)

    return UserSkillState(
        user_id=state.user_id,
        skill_slug=state.skill_slug,
        mastery_score=mastery,
        confidence=confidence,
        evidence_count=state.evidence_count,
        recent_error_count=state.recent_error_count,
        distinct_question_ids=state.distinct_question_ids,
        last_seen_at=state.last_seen_at,
        last_reviewed_at=state.last_reviewed_at,
        status=mastery_for_status(mastery),
        trend=derive_trend(state.mastery_score, mastery),
    )


def should_be_reviewed(state: UserSkillState, now: datetime) -> bool:
    status = mastery_for_status(state.mastery_score)
    if status in (SkillStatus.STRONG, SkillStatus.NEW):
        return False
    if state.recent_error_count >= 3:
        return True
    if state.last_seen_at is not None:
        inactive_days = max(
            0.0,
            (_as_utc(now) - _as_utc(state.last_seen_at)).total_seconds() / 86400.0,
        )
        if inactive_days > MAX_INACTIVE_DAYS:
            return True
    return False


def recommend(
    states: Dict[str, UserSkillState],
    skill_names: Dict[str, str],
    prerequisites: Dict[str, List[str]],
    question_by_skill: Dict[str, List[str]],
    now: datetime,
    limit: int = 5,
) -> List[Recommendation]:
    """Rank recommended skills for a user.

    Rules (deterministic):
    1. A skill missing a non-strong prerequisite is blocked until the weakest
       prerequisite is practiced — the prerequisite itself is recommended.
    2. Skills due for review rank above developing skills, which rank above
       learning skills.
    3. New skills (no evidence) rank lowest among candidates.
    4. Recommendations carry an explanation and, when available, a question.
    """
    ordered = []
    for slug in skill_names:
        state = states.get(slug)
        missing_prereq = _weakest_missing_prerequisite(
            slug, states, prerequisites, skill_names
        )
        if missing_prereq is not None:
            prereq_state = states.get(missing_prereq)
            # A brand-new prerequisite is "start learning", not "master first".
            if prereq_state is None:
                ordered.append((missing_prereq, RecommendationReason.NEW_SKILL))
            else:
                ordered.append(
                    (missing_prereq, RecommendationReason.MISSING_PREREQUISITE)
                )
            continue
        if state is None:
            ordered.append((slug, RecommendationReason.NEW_SKILL))
            continue
        status = mastery_for_status(state.mastery_score)
        if should_be_reviewed(state, now):
            ordered.append((slug, RecommendationReason.DUE_FOR_REVIEW))
            continue
        if status in (SkillStatus.DEVELOPING, SkillStatus.LEARNING):
            ordered.append((slug, RecommendationReason.WEAK_SKILL))
            continue
        if status == SkillStatus.STRONG and state.evidence_count < 3:
            ordered.append((slug, RecommendationReason.STRENGTHEN))

    # Stable priority ordering: review > missing prereq > weak > strengthen > new.
    rank = {
        RecommendationReason.DUE_FOR_REVIEW: 4,
        RecommendationReason.MISSING_PREREQUISITE: 3,
        RecommendationReason.WEAK_SKILL: 2,
        RecommendationReason.STRENGTHEN: 1,
        RecommendationReason.NEW_SKILL: 0,
    }
    ordered.sort(key=lambda item: rank[item[1]], reverse=True)

    results: List[Recommendation] = []
    for slug, reason in ordered:
        if len(results) >= limit:
            break
        if slug in (r.skill_slug for r in results):
            continue
        name = skill_names.get(slug, slug)
        question = (question_by_skill.get(slug) or [None])[0]
        results.append(
            Recommendation(
                skill_slug=slug,
                name=name,
                reason=reason,
                reason_text=_reason_text(reason, name, state=states.get(slug)),
                suggested_question_id=question,
            )
        )
    return results


def _reason_text(
    reason: RecommendationReason, name: str, state: Optional[UserSkillState]
) -> str:
    if reason == RecommendationReason.MISSING_PREREQUISITE:
        return f"Master {name} first; it unlocks other skills."
    if reason == RecommendationReason.DUE_FOR_REVIEW:
        return f"{name} is due for review to prevent forgetting."
    if reason == RecommendationReason.WEAK_SKILL:
        return f"{name} needs practice to become a strength."
    if reason == RecommendationReason.STRENGTHEN:
        return f"Reinforce {name} with one more independent solve."
    return f"Start learning {name}."


def _weakest_missing_prerequisite(
    slug: str,
    states: Dict[str, UserSkillState],
    prerequisites: Dict[str, List[str]],
    skill_names: Dict[str, str],
) -> Optional[str]:
    for prereq in prerequisites.get(slug, []):
        if prereq not in skill_names:
            continue
        state = states.get(prereq)
        if (
            state is None
            or mastery_for_status(state.mastery_score) != SkillStatus.STRONG
        ):
            return prereq
    return None
