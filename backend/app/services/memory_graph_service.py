"""MemoryGraphService — derives the forgetting-curve dashboard (Idea #3).

Read-only aggregation over review cards + submissions joined to question
categories. No new table; pure Python over existing ports so the
derivation is deterministic and cheap (<=109 questions).

Energy cost models the "5-min now vs 30-min later" copy: it grows with
the SM-2 interval and with lapses so the most-urgent topic sorts first.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

from app.models.memory_schemas import MemoryGraphResponse, TopicMemory


class MemoryGraphService:
    def __init__(self, *, review_repo, question_repo, submission_repo):
        self.review_repo = review_repo
        self.question_repo = question_repo
        self.submission_repo = submission_repo

    async def graph(self, *, user_id: str, now: datetime) -> MemoryGraphResponse:
        # Build question_id -> category map.
        questions = await self.question_repo.get_all()
        q_to_cat: Dict[str, str] = {q.id: q.category for q in questions}

        # Fetch all review cards for the user. Prefer the efficient
        # list_for_user if the repo exposes it; fall back to per-question
        # fan-out for older fakes/mocks.
        if hasattr(self.review_repo, "list_for_user"):
            all_cards = list(await self.review_repo.list_for_user(user_id))  # type: ignore[attr-defined]
        else:
            all_cards = []
            for qid in q_to_cat:
                all_cards.extend(await self.review_repo.list_for_question(user_id, qid))

        # Submissions for recency.
        submissions = list(await self.submission_repo.list_by_user(user_id, limit=1000))

        # Map topic -> last touch (max of submission created_at and card last_reviewed_at)
        topic_last_touch: Dict[str, datetime] = {}
        # From submissions
        for sub in submissions:
            cat = q_to_cat.get(sub.question_id)
            if not cat:
                continue
            ts = sub.created_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if cat not in topic_last_touch or ts > topic_last_touch[cat]:
                topic_last_touch[cat] = ts
        # From cards last_reviewed_at only (submission coverage is primary).
        for card in all_cards:
            cat = q_to_cat.get(card.question_id)
            if not cat:
                continue
            ts_candidate = card.last_reviewed_at
            if ts_candidate is None:
                continue
            ts = ts_candidate
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if cat not in topic_last_touch or ts > topic_last_touch[cat]:
                topic_last_touch[cat] = ts

        # Group cards by topic.
        grouped: Dict[str, List] = defaultdict(list)
        for card in all_cards:
            cat = q_to_cat.get(card.question_id)
            if not cat:
                continue
            grouped[cat].append(card)

        topics: List[TopicMemory] = []
        total_due = 0
        for topic, cards in grouped.items():
            due = sum(1 for c in cards if c.state == "scheduled" and c.due_at <= now)
            total_due += due
            intervals = [c.interval_days for c in cards]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            lapses = sum(c.lapses for c in cards)
            # Energy cost: interval weight + lapses penalty + due pressure.
            energy = int(avg_interval * 3 + lapses * 5 + due * 2 + 1)
            last = topic_last_touch.get(topic)
            days_since = (now - last).days if last else None
            if days_since is not None and days_since < 0:
                days_since = 0
            topics.append(
                TopicMemory(
                    topic=topic,
                    totalCards=len(cards),
                    dueCount=due,
                    avgIntervalDays=round(avg_interval, 2),
                    daysSinceLastTouch=days_since,
                    lapseCount=lapses,
                    energyCostMinutes=energy,
                    cardIds=[c.id for c in cards],
                )
            )

        # Most urgent first (highest energy), then due count, then topic name.
        topics.sort(key=lambda t: (-t.energyCostMinutes, -t.dueCount, t.topic))

        total_cards = len(all_cards)
        oldest_due = None
        if total_due:
            due_cards = [c for c in all_cards if c.state == "scheduled" and c.due_at <= now]
            if due_cards:
                oldest = min(c.due_at for c in due_cards)
                oldest_due = max(0, (now - oldest).days)

        return MemoryGraphResponse(
            topics=topics,
            totalDue=total_due,
            totalCards=total_cards,
            oldestDueDays=oldest_due,
        )
